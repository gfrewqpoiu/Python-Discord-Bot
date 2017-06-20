#!/usr/bin/env python3
import sys
try:
    import discord
    from discord.ext import commands
    from discord import utils
    import asyncio
except:
    raise ModuleNotFoundError("You don't have Discord.py installed, install it with 'pip3 install --user discord.py[voice]'")
try:
    import pyrandom as trandom
except:
    {}
import random
import configparser
from googleapiclient.discovery import build
from pprint import pprint


config = configparser.ConfigParser()
config.read('config.ini')
login = config['Login']
settings = config['Settings']
rngcfg = config['Randomness']
googlekey=settings.get('Google API Key', '')


bot = commands.Bot(command_prefix=settings.get('prefix', '$'), description=settings.get('Bot Description', 'A WIP bot'), pm_help=True)

loginID = login.get('Login Token')
mainChannelID = settings.get('Main Channel', '')
randomAPIKey = rngcfg.get('Random.org Key', '')
randomAPIUse = rngcfg.getboolean('Use Random.org', False)

# Do not edit anything after this line if you simply want to run this bot

search_engine_id="018084019232060951019:hs5piey28-e"

def _checkrandom():
    """Checks for the used randomness API"""
    if randomAPIKey != '' and randomAPIUse:
        try:
            trandom.set_api_key(randomAPIKey)
            return True
        except:
            return False
    else:
        return False

if _checkrandom():
    truerandom = True  # Do not edit this
else:
    truerandom = False  # Do not edit this

mainchannel = None  # Do not edit this
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    mainchannel = bot.get_channel(mainChannelID)
    joinmsg = None
    try:
       joinmsg = await bot.send_message(mainchannel, 'I am online!')
    except:
        print("There was no Main Channel specified or I couldn't find it")
    if truerandom:
        print("I am using random.org for random numbers")
    else:
        print("I am not using random.org for random numbers")
    print('------')
    if joinmsg != None:
        await asyncio.sleep(10)
        await bot.delete_message(joinmsg)


@bot.command(pass_context=True)
async def msgs(ctx):
    """Calculates messages from you in this chat"""
    counter = 0
    tmp = await bot.say('Calculating messages...')
    await bot.type()
    async for log in bot.logs_from(ctx.message.channel, limit=100):
        if log.author == ctx.message.author:
            counter += 1

    await bot.reply('You have {} messages.'.format(counter), delete_after=10)


@bot.command()
async def sleep():
    """Makes the bot sleep for 5 seconds"""
    await asyncio.sleep(5)
    await bot.say('Done sleeping', delete_after=10)

@bot.command()
async def random(min: int=1, max: int=6, numbers: int=1):
    """Uses a random number generator to generate numbers for you"""

    if min >= max:
        await bot.say("You entered incorrect values for min and max, use `random min max numbers`")
        return

    if truerandom:
        try:
            results = trandom.generate_integers(n=numbers, min=min, max=max)
            result = ''.join(str(results))
            await bot.say(result + " provided by random.org")
        except:
            result = ''
            for i in range(1, numbers):
                result = result + " " + str(random.randint(min, max))
                await bot.say(result)
    else:
        result = ''
        for i in range(1, numbers):
            result = result + " " + str(random.randint(min, max))
            await bot.say(result)

@bot.command()
async def rng(min: int=1, max: int=100, numbers: int=3):
    """Uses a random number generator to generate numbers for you"""
    if min >= max:
        await bot.say("You entered incorrect values for min and max, use `random min max numbers`")
        return

    if truerandom:
        try:
            results = trandom.generate_integers(n=numbers, min=min, max=max)
            result = ''.join(str(results))
            await bot.say(result + " provided by random.org")
        except:
            result = ''
            for i in range(1, numbers):
                result = result + " " + str(random.randint(min, max))
                await bot.say(result)
    else:
        result = ''
        for i in range(1, numbers):
            result = result + " " + str(random.randint(min, max))
            await bot.say(result)

@bot.command(pass_context=True)
async def shutdown(ctx):
    """Shuts the bot down"""
    await bot.say("Shutting down!", delete_after=3)
    await asyncio.sleep(5)
    print(f"Shutting down on request of {ctx.message.author.name}!")
    await bot.close()
    try:
        sys.exit()
    except:
        {}

@bot.command(pass_context=True)
async def hello(ctx):
    """Says Hello"""
    await bot.say(f"Hello {ctx.message.author.mention}!")

@bot.command()
async def img(query: str):
    """Searches for an Image on Google and returns the first result"""
    if googlekey=='':
        await bot.say("No google api key specified!")
        return

    service = build("customsearch", "v1", developerKey=googlekey)

    res=service.cse().list(
        q=query,
        cx=search_engine_id,
        num=1,
        fields="items(image(contextLink,thumbnailLink),link)",
        safe='high',
        searchType='image'
    ).execute()
    pprint(res)
    await bot.say(f"Searched for {query}. Look to the console for the result")

try:
    bot.run(loginID)
except:
    raise ValueError("Couldn't log in with the given credentials, please check those in config.ini and your connection and try again!")
