#!/usr/bin/env python3
import random
import configparser
import sys
import os
import subprocess
import checks
import urllib
import pprint
try:  # These are mandatory.
    import discord
    from discord.ext import commands
    from discord import utils
    import asyncio
except:
    raise ModuleNotFoundError(
        "You don't have Discord.py installed, install it with 'pip3 install --user --upgrade discord.py[voice]'")

try:
    import requests
except:
    print("You don't have requests installed. No URL shortening or Search commands will work")

# Import the Config file
config = checks.getconf()
login = config['Login']
settings = config['Settings']
rngcfg = config['Randomness']
searchcfg = config['Search']

# Setup some Variables
userandomAPI = rngcfg.getboolean('Use Random.org', False)
usegoogleAPI = searchcfg.getboolean('Use Google Image Search', False)
loginID = login.get('Login Token')
mainChannelID = settings.get('Main Channel', '')
provideSearch = False
provideRandomOrg = False
mainchannel = None

# Check for optional features
if userandomAPI:
    randomAPIKey = rngcfg.get('Random.org Key', '')
    randomAPIKey.strip()
    if randomAPIKey:
        try:
            import pyrandom as trandom
            trandom.set_api_key(randomAPIKey)
            provideRandomOrg = True
        except:
            pass

if usegoogleAPI:
    googlekey = searchcfg.get('Google API Key', '')
    googlekey.strip()
    if googlekey:
        try:
            from googleapiclient.discovery import build
            from urllib import parse
            search_engine_id = "018084019232060951019:hs5piey28-e"
            provideSearch = True
        except:
            pass

if provideSearch:
    searchservice = build("customsearch", "v1", developerKey=googlekey)


# Utility functions
async def getimage(query: str, start: int=1):
    return searchservice.cse().list(
        q=query,
        cx=search_engine_id,
        num=1,
        fields="items(image(contextLink),link)",
        safe='high',
        searchType='image',
        start=start
    ).execute()


async def getrandints(minimum: int=1, maximum: int=6, amount: int=1, force_builtin: bool=True):
    if minimum < maximum and 50 >= amount > 0:
        if provideRandomOrg and not force_builtin:
            try:
                results = trandom.generate_integers(
                    n=amount, min=minimum, max=maximum)
                result = ''.join(str(results))
                return result.strip() + " provided by random.org"

            except:
                result = ''
                for i in range(0, amount):
                    result += str(random.randint(minimum, maximum)) + " "

                return result.strip()

        else:
            result = ''
            for i in range(0, amount):
                result += str(random.randint(minimum, maximum)) + " "

            return result.strip()

    elif minimum >= maximum:
        raise ValueError("Minimum needs to be smaller than Maximum")
    else:
        raise ValueError(
            "You need to request at least one and a max of 50 ints")


def is_valid_url(url):
    qualifying = ('scheme', 'netloc')
    token = parse.urlparse(url)
    return all([getattr(token, qualifying_attr)
                for qualifying_attr in qualifying])


bot = commands.Bot(command_prefix=settings.get('prefix', '$'),
                   description=settings.get('Bot Description', 'A WIP bot'), pm_help=True)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    try:
        mainchannel = bot.get_channel(mainChannelID)
    except:
        print("There was no Main Channel specified or I couldn't find it")

    if provideRandomOrg:
        print("Using random.org for random numbers")
    else:
        print("Not using random.org for random numbers")

    if provideSearch:
        print("Image Search activated")
    else:
        print("Image Search deactivated")

    print('------')

    print("I am part of the following servers:")
    for server in bot.servers:
        print(f"{server.name}")

    print('------')


@bot.command(pass_context=True)
async def msgs(ctx):
    """Calculates messages from you in this chat"""
    counter = 0
    tmp = await bot.say('Calculating messages...')
    await bot.type()
    async for log in bot.logs_from(ctx.message.channel, limit=100):
        if log.author == ctx.message.author:
            counter += 1

    await bot.delete_message(ctx.message)
    await bot.reply(f'You have {counter} messages.', delete_after=10)


@bot.command(pass_context=True)
async def timer(ctx, seconds: int=5):
    """Pings you when the given amount of seconds is over
        This doesn't work over restarts"""
    await bot.say("Okay, I will remind you!", delete_after=seconds)
    await asyncio.sleep(seconds)
    await bot.say(f'{ctx.message.author.mention}, your {seconds} seconds timer is up', delete_after=10)
    await bot.delete_message(ctx.message)


@bot.command()
async def rng(min: int=1, max: int=6, amount: int=3):
    """Uses a random number generator to generate numbers for you
        If the bot owner has specified a random.org API key the numbers will come from there.
        Params: min: Minimum value (inclusive)
                max: Maximum value (inclusive)
                amount: amount of Numbers to generate"""
    result = await getrandints(minimum=min, maximum=max, amount=amount, force_builtin=False)
    await bot.say(str(result))

if provideRandomOrg:
    @bot.command()
    async def rnglocal(min: int=1, max: int=100, amount: int=3):
        """Uses the local random number generator to generate numbers for you
            Unlike the rng command this will never use random.org.
            Params: min: Minimum value (inclusive)
                    max: Maximum value (inclusive)
                    amount: amount of Numbers to generate"""
        result = await getrandints(minimum=min, maximum=max, amount=amount, force_builtin=True)
        await bot.say(str(result))


@bot.command()
async def dice(amount: int=1):
    """Uses a random number generator to roll dice for you
        Parameter amount: Amount of dice to roll"""
    result = await getrandints(amount=amount, force_builtin=False)
    await bot.say(str(result))


@bot.command(pass_context=True)
async def hello(ctx):
    """Says Hello"""
    await bot.say(f"Hello {ctx.message.author.mention}!", delete_after=10)
    await asyncio.sleep(10)
    await bot.delete_message(ctx.message)


@checks.is_owner()
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


@checks.is_owner()
@bot.command(pass_context=True)
async def update(ctx):
    """Updates the bot with the newest Version from GitHub
        Only works for the bot owner account"""
    await bot.say("Ok, I am updating from GitHub")
    try:
        output = subprocess.run(["git", "pull"], stdout=subprocess.PIPE)
        embed = discord.Embed()
        embed.set_author(name="Output:")
        embed.set_footer(text=output.stdout.decode('utf-8'))
        await bot.send_message(ctx.message.channel, embed=embed)
    except:
        await bot.say("That didn't work for some reason")

if provideSearch:
    @bot.command(pass_context=True)
    async def img(ctx, *, query: str=""):
        """Searches for an Image on Google and returns the first result"""
        query.strip()
        await bot.delete_message(ctx.message)
        if not query:
            await bot.say("Please provide a search term")
            return

        queryurl = parse.quote_plus(query)
        res = await getimage(query)
        link = res['items'][0]['link']

        embed = discord.Embed()
        embed.set_image(url=str(link))
        embed.set_author(name=f"Image Search for {query} by {ctx.message.author.name}",
                         url=f"https://www.google.com/search?q={queryurl}&source=lnms&tbm=isch")

        await bot.send_message(ctx.message.channel, embed=embed)

    @bot.command(pass_context=True)
    async def rimg(ctx, *, query: str = ""):
        """Searches for an Image on Google and returns a random result"""
        query.strip()
        await bot.delete_message(ctx.message)
        if not query:
            await bot.say("Please provide a search term")
            return

        queryurl = parse.quote_plus(query)
        start = await getrandints(maximum=50)
        res = await getimage(query, start=int(start))
        link = res['items'][0]['link']

        embed = discord.Embed()
        embed.set_image(url=str(link))
        embed.set_author(name=f"Image Search for {query} by {ctx.message.author.name}",
                         url=f"https://www.google.com/search?q={queryurl}&source=lnms&tbm=isch")

        await bot.send_message(ctx.message.channel, embed=embed)


@checks.is_owner()
@bot.command(pass_context=True)
async def restart(ctx):
    """Restart the bot"""
    await bot.say("Restarting", delete_after=3)
    await asyncio.sleep(5)
    print(f"Restarting on request of {ctx.message.author.name}!")
    await bot.close()
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except:
        pass


@bot.command()
async def shorten(url: str):
    """Shortens the given URL with v.gd
    Requires the URL to begin with e.g https://
    data:// is unsupported"""
    if not is_valid_url(url=url):
        await bot.say("No valid URL specified!")
        return
    urltoshorten = parse.quote(string=url)
    result = requests.get(
        f"https://v.gd/create.php?format=simple&url={urltoshorten}")
    await bot.say(f"{result.text}")


try:
    bot.run(loginID)
except:
    raise ValueError(
        "Couldn't log in with the given credentials, please check those in config.ini and your connection and try again!")
