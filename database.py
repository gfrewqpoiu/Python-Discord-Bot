import datetime
from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase
import asyncio

database = SqliteQueueDatabase(
    'bot.db',
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,  # The worker thread must not be started manually.
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0)
sqlite = True

async def shutdown():
    if sqlite:
        database.stop()
        database.close()
    else:
        database.close()

class Image(Model):
    link=TextField()
    channelID=CharField()
    channelName=CharField()
    searchQuery=TextField()
    userID=CharField()
    userName=CharField()
    timestamp=DateTimeField(default=datetime.datetime.now)

class ShortLink(Model):
    originalURL=TextField()
    shortenedURL=CharField(unique=True)
    isDirectLink=BooleanField(default=False)

