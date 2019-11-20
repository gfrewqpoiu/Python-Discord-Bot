#!/usr/bin/env python3
import random
import sys
import os
import subprocess
import checks
import logging
from loguru import logger
try:  # These are mandatory.
    import discord
    from discord.ext import commands
    from discord import utils
    import asyncio
    import aiohttp
except ImportError:
    raise ModuleNotFoundError(
        "You don't have Discord.py installed, install it with "
        "'pip3 install --user --upgrade discord.py[voice]'")

try:
    import httpx
except ImportError:
    logger.warning("You don't have httpx installed. No URL shortening or Search commands will work")

try:
    import deepl
    provideTranslation = True
except ImportError:
    logger.warning("You don't have pydeepl installed. Translation will not work!")
    provideTranslation = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Retrieve context where the logging call occurred, this happens to be in the 6th frame upward
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=logging.WARNING)

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
provideYoutubedl = False
peewee_available = False
bot_version = "4.0.0a"

# Check for optional features
if userandomAPI:
    randomAPIKey = rngcfg.get('Random.org Key', '')
    randomAPIKey.strip()
    if randomAPIKey:
        from RandomOrgAPIClient import RandomOrgClient
        trandom = RandomOrgClient(randomAPIKey)
        provideRandomOrg = True

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

try:
    import youtube_dl
    provideYoutubedl = True
except:
    pass

try:
    import peewee
    import database
    db = database.createdb()
    peewee_available = True
except:
    db = None
    pass

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

async def downloadfile(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            return await resp.read()

async def getrandints(minimum: int=1, maximum: int=6, amount: int=1, force_builtin: bool=True):
    if minimum < maximum and 50 >= amount > 0:
        if provideRandomOrg and not force_builtin:
            try:
                logger.debug("Using Random.Org to fetch random Numbers")
                results = await trandom.generateIntegers(
                    amount=amount, min=minimum, max=maximum)
                result = ''.join(str(results))
                return result.strip() + " provided by random.org"

            except:
                logger.warning("Failed to use Random.org for number generation, falling back to local RNG.")
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


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now uploading...')

ydlU_opts = {
            'postprocessors': [{
                'key': 'ExecAfterDownload',
                'exec_cmd': 'rclone move {} Drive:Upload',
            }],
            'progress_hooks': [my_hook],
            'outtmpl': '%(title)s.%(ext)s',
        }

ydlvU_opts = {
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {
                'key': 'ExecAfterDownload',
                'exec_cmd': 'rclone move {} Drive:Upload',
            }
            ],
            'progress_hooks': [my_hook],
            'outtmpl': '%(title)s.%(ext)s',
        }


ydl_opts = {
            'progress_hooks': [my_hook],
            'outtmpl': '%(title)s.%(ext)s',
        }

ydlv_opts = {
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [my_hook],
            'outtmpl': '%(title)s.%(ext)s',
        }

def _downloadU(url, isVideo: bool=True):
    with youtube_dl.YoutubeDL(ydlvU_opts) as ydl:
        ydl.download([url])
        return url

def _downloadaU(url):
    with youtube_dl.YoutubeDL(ydlU_opts) as ydl:
        ydl.download([url])
        return url

def _download(url, isVideo: bool=True):
    with youtube_dl.YoutubeDL(ydlv_opts) as ydl:
        ydl.download([url])
        return url

def _downloada(url):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return url

async def _shorten(url, direct=False):
    """Shortens a given URL using v.gd
    if direct is set to true it will use is.gd for a direct link instead"""

    if direct:
        url = parse.quote(string=url)
        result = httpx.get(
            f"https://is.gd/create.php?format=simple&url={url}")
        return result.text
    else:
        url = parse.quote(string=url)
        result = httpx.get(
            f"https://v.gd/create.php?format=simple&url={url}")
        return result.text


async def _imagesearch(ctx, query, start=1):
    """Searches for an image and returns a discord embed"""
    query.strip()
    try:
        await ctx.message.delete()
    except:
        pass
    if not query:
        await ctx.send("Please provide a search term")
        return

    queryurl = parse.quote_plus(query)
    result = await getimage(query, start)
    link = result['items'][0]['link']

    embed = discord.Embed()
    embed.set_image(url=str(link))
    embed.set_author(name=f"Image Search for {query} by {ctx.message.author.name}",
                     url=f"https://www.google.com/search?q={queryurl}&source=lnms&tbm=isch")
    return embed


bot = commands.Bot(command_prefix=settings.get('prefix', '$'),
                   description=settings.get('Bot Description', 'A WIP bot'), pm_help=True)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(f"Using Bot Version: {bot_version}")
    try:
        bot.get_channel(mainChannelID)
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

    if provideYoutubedl:
        print("YouTube.dl detected")
    else:
        print("No YouTube.dl detected")

    print('------')

    print("I am part of the following servers:")
    for guild in bot.guilds:
        print(f"{guild.name} with {guild.member_count} members")

    print('------')


@bot.command()
async def msgs(ctx):
    """Calculates messages from you in this chat"""
    counter = 0
    tmp = await ctx.send('Calculating messages...')
    await ctx.trigger_typing()
    async for message in ctx.history(limit=200):
        if message.author == ctx.author:
            counter += 1

    await ctx.message.delete()
    await tmp.delete()
    await ctx.send(f'You have {counter} messages.', delete_after=10)


@bot.command(aliases=['remind'])
async def timer(ctx, seconds: int = 5):
    """Pings you when the given amount of seconds is over
        This doesn't work over restarts."""
    await ctx.send("Okay, I will remind you!", delete_after=seconds)
    await asyncio.sleep(seconds)
    await ctx.send(f'{ctx.message.author.mention}, your {seconds} seconds timer is up', delete_after=10)
    await ctx.message.delete()


@bot.command(aliases=['random', 'randint'])
async def rng(ctx, min: int = 1, max: int = 6, amount: int = 3):
    """Uses a random number generator to generate numbers for you
        If the bot owner has specified a random.org API key the numbers will come from there.
        Params: min: Minimum value (inclusive)
                max: Maximum value (inclusive)
                amount: amount of Numbers to generate"""
    result = await getrandints(minimum=min, maximum=max, amount=amount, force_builtin=False)
    await ctx.send(str(result))

if provideRandomOrg:
    @bot.command(hidden=True, aliases=['randomlocal', 'rngl', 'randlocal'])
    async def rnglocal(ctx, min: int=1, max: int=100, amount: int=3):
        """Uses the local random number generator to generate numbers for you
            Unlike the rng command this will never use random.org.
            Params: min: Minimum value (inclusive)
                    max: Maximum value (inclusive)
                    amount: amount of Numbers to generate"""
        result = await getrandints(minimum=min, maximum=max, amount=amount, force_builtin=True)
        await ctx.send(str(result))


@bot.command()
async def dice(ctx, amount: int=1, sides: int=6):
    """Uses a random number generator to roll dice for you
        Parameters amount: Amount of dice to roll
                   sides: how many sides the dice has."""
    result = await getrandints(maximum=sides, amount=amount, force_builtin=False)
    await ctx.send(str(result))


@bot.command(aliases=['hi'])
async def hello(ctx):
    """Says Hello"""
    await ctx.send(f"Hello {ctx.message.author.mention}!", delete_after=10)
    await asyncio.sleep(10)
    await ctx.message.delete()


@checks.is_owner()
@bot.command(hidden=True)
async def shutdown(ctx):
    """Shuts the bot down"""
    await ctx.send("Shutting down!", delete_after=3)
    await asyncio.sleep(5)
    print(f"Shutting down on request of {ctx.message.author.name}!")
    await bot.close()
    try:
        sys.exit()
    except:
        {}


@checks.is_owner()
@bot.command(hidden=True)
async def update(ctx):
    """Updates the bot with the newest Version from GitHub
        Only works for the bot owner account
        This doesn't work when git isn't installed"""
    await ctx.send("Ok, I am updating from GitHub", delete_after=5)
    try:
        output = subprocess.run(["git", "pull"], stdout=subprocess.PIPE)
        embed = discord.Embed()
        embed.set_author(name="Output:")
        embed.set_footer(text=output.stdout.decode('utf-8'))
        await ctx.send(embed=embed)
    except:
        await ctx.send("That didn't work for some reason", delete_after=10)

if provideSearch:
    @bot.command(aliases=['image'])
    async def img(ctx, *, query: str=""):
        """Searches for an Image on Google and returns the first result"""
        message = ctx.message
        embed = await _imagesearch(ctx, query)
        await ctx.send(embed=embed)

    @bot.command(aliases=['randomimage'])
    async def rimg(ctx, *, query: str=""):
        """Searches for an Image on Google and returns a random result"""
        start = await getrandints(maximum=50)
        embed = await _imagesearch(ctx, query, start)
        await ctx.send(embed=embed)


@checks.is_owner()
@bot.command(hidden=True, aliases=['reboot'])
async def restart(ctx):
    """Restart the bot"""
    await ctx.send("Restarting", delete_after=3)
    await asyncio.sleep(5)
    print(f"Restarting on request of {ctx.message.author.name}!")
    await bot.close()
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except:
        pass


@bot.command(aliases=['vgd'])
async def shorten(ctx, url: str):
    """Shortens the given URL with v.gd
    Requires the URL to begin with e.g https://
    data:// is unsupported"""
    if not is_valid_url(url=url):
        await ctx.send("No valid URL specified!")
        return
    result = await _shorten(url)
    await ctx.send(f"{result}")


@bot.command(aliases=['isgd', 'shortendl'], hidden=True)
async def shortendirect(ctx, url: str):
    """Shortens the given URL with is.gd for a direct link.
    Requires the URL to begin with e.g https://
    data:// is unsupported.
    Shorten Command should be preferred."""
    if not is_valid_url(url=url):
        await ctx.send("No valid URL specified!")
        return
    result = await _shorten(url)  # ,direct=True)
    await ctx.send(f"{result}")


@bot.command(hidden=True)
async def version(ctx):
    """Gives back the bot version"""
    await ctx.send(bot_version)

if provideYoutubedl:
    @checks.is_owner()
    @bot.command(hidden=True, aliases=['dlaul'])
    async def downloadaudioandupload(ctx, url: str):
        """This downloads the audio (or video) from the given link and uploads it to rclones Drive:Upload folder.
        This should work for most sites. Read the youtube-dl docs for the full list."""
        await ctx.send(f"Okay i am downloading the audio at {url} and uploading it to your drive!")
        await bot.loop.run_in_executor(None, _downloadaU, url)
        await ctx.send('Done!')

    @checks.is_owner()
    @bot.command(hidden=True, aliases=['dlvul', 'dlul'])
    async def downloadvideoandupload(ctx, url: str):
        """This downloads a video from the given link and uploads it to rclones Drive:Upload folder.
        This command also converts the video to MP4 if it isn't in that format already.
        So it is not advisable to use this for audio files. use dla instead.
        This shoud work for most sites. Read the youtube-dl docs for the full list.
        I recommend having ffmpeg installed and in your path."""
        await ctx.send(f"Okay i am downloading the video at {url} and uploading it to your drive!")
        await bot.loop.run_in_executor(None, _downloadU, url)
        await ctx.send('Done!')

    @checks.is_owner()
    @bot.command(hidden=True, aliases=['dla'])
    async def downloadaudio(ctx, url: str):
        """This downloads the audio (or video) from the given link and saves it in the bot folder.
        This should work for most sites. Read the youtube-dl docs for the full list."""
        await ctx.send(f"Okay i am downloading the audio at {url}")
        await bot.loop.run_in_executor(None, _downloada, url)
        await ctx.send('Done!')

    @checks.is_owner()
    @bot.command(hidden=True, aliases=['dlv', 'dl'])
    async def downloadvideo(ctx, url: str):
        """This downloads a video from the given link and saves it in the folder where the bot is located.
        This command also converts the video to MP4 if it isn't in that format already.
        So it is not advisable to use this for audio files. use dla instead.
        This shoud work for most sites. Read the youtube-dl docs for the full list.
        I recommend having ffmpeg installed and in your path."""
        await ctx.send(f"Okay i am downloading the video at {url}")
        await bot.loop.run_in_executor(None, _download, url)
        await ctx.send('Done!')

if provideTranslation:
    @bot.command(aliases=['trans', 'tl'])
    async def translate(ctx, *, translate: str):
        """Translates the given Text into the given language.
           Usage: EN Text
           where EN is a Language shorthand like DE EN NL etc
           Translation is provided by DeepL"""
        try:
            translated, extra_data = deepl.translate(target=translate[0].upper()+translate[1].upper(), text=translate[3:])
        except:
            translated = "The Text was not given in the proper format: EN Text"
        await ctx.send(translated)

if peewee_available:
    @checks.is_owner()
    @bot.command(aliases=['qaddf'])
    async def quoteaddfile(ctx, name: str):
        """Creates a new Quote with the given attachment.
        Attach a file to the command that you run."""
        attachment = ctx.message.attachments[0]
        url = attachment['url']
        database.createLinkQuote(ctx.message.author, name=name, link=url)
        await ctx.send("Done")

    @checks.is_owner()
    @bot.command(aliases=['qadd'])
    async def quoteadd(ctx, name: str, text: str):
        """Adds a text quote into the bot database."""
        try:
            database.createTextQuote(ctx.message.author, name=name, text=text)
        except peewee.IntegrityError:
            return await ctx.send("This quote couldn't be added. Most likely the keyword is taken.")
        except Exception as e:
            logging.log(level=logging.ERROR, msg=e)
            return await ctx.send("There was a weird error. Inform the bot Owner.")
        await ctx.send("Done")

    @bot.command(aliases=['q'])
    async def quote(ctx, name: str):
        """Posts the Quote with the given name in the chat."""
        await ctx.message.delete()
        try:
            quote = database.Quote.get(name=name)
        except peewee.DoesNotExist:
            return await ctx.send("This doesn't exist")

        if quote.text:
            await ctx.send("📢 " + quote.text)
            quote.times_used += 1
        else:
            await ctx.send("📢 " + quote.link)
        quote.times_used += 1


@bot.command()
async def ping(ctx):
    """Checks the ping of the bot"""
    m = await ctx.send("Ping?")
    await m.edit(f"Pong, Latency is {m.timestamp - ctx.message.timestamp}.")


# @bot.command(hidden=True, aliases=['setgame', 'setplaying'])
# @commands.has_permissions(administrator=True)
# async def gametitle(ctx, *, message: str):
#     """Sets the currently playing status of the bot"""
#     await bot.change_presence(game=discord.Game(name=message))
#     await ctx.send(f"Changed the playing status to {message}")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def changelog(ctx):
    """Gives back the changelog for the most recent non bugfix build. Full changelog is in Changelog.md"""
    await ctx.send("""4.0.0a Rewrite to allow the usage of discordpy 1.0 and newer.
    3.2.1 Added some commands to just download files with youtube.dl (dla and dlv)""")

if __name__ == '__main__':
    try:
        bot.run(loginID)
    except:
        raise ValueError(
            "Couldn't log in with the given credentials, please check those in config.ini"
            " and your connection and try again!")

