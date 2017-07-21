import datetime
from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase
import asyncio
import checks

dbconfig = checks.getdb()

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy

if dbconfig.get('Database Type', 'SQLite') != 'MEMORY':
    database = SqliteQueueDatabase(
        'bot.db',
        use_gevent=False,  # Use the standard library "threading" module.
        # The worker thread doesn't need to be started manually.
        autostart=True,
        queue_max_size=64,  # Max. # of pending writes that can accumulate.
        results_timeout=5.0)
    sqlite = True
else:
    database = SqliteQueueDatabase(':memory:', autostart=True, queue_max_size=10, results_timeout=5.0)

database_proxy.initialize(database)
db = database


async def shutdown():
    if sqlite:
        db.stop()
        db.close()
    else:
        db.close()


class Image(BaseModel):
    link = TextField()
    channelID = CharField()
    channelName = CharField()
    searchQuery = TextField()
    userID = CharField()
    userName = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    wasRandom = BooleanField(default=False)


class ShortLink(BaseModel):
    originalURL = TextField()
    shortenedURL = CharField(unique=True)
    isDirectLink = BooleanField(default=False)


def createTables():
    db.create_tables([Image, ShortLink], True)

async def saveImage(ctx, link, query, wasRandom: bool=False):
    return Image.create(link=link,
                         channelID=ctx.message.channel.id,
                         channelName=ctx.message.channel.name,
                         searchQuery=query,
                         userID=ctx.message.author.id,
                         userName=ctx.message.author.name,
                         wasRandom=wasRandom)