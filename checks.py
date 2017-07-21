from discord.ext import commands
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def getconf():
    return config


def getdb():
    return config['Database']


settings = config['Settings']

configOwner = settings.get('Owner ID')


def is_owner_check(message):
    return message.author.id == configOwner


def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))

# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# Of course, the owner will always be able to execute commands.


def check_permissions(ctx, perms):
    msg = ctx.message
    if is_owner_check(msg):
        return True

    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())
