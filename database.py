import datetime
from peewee import *
from playhouse.sqliteq import SqliteQueueDatabase

database = SqliteQueueDatabase(
    'bot.db',
    use_gevent=False,  # Use the standard library "threading" module.
    autostart=True,  # The worker thread now must be started manually.
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0)

class Image(Model):
    link=TextField()
    channelID=CharField()
    channelName=CharField()
    searchQuery=TextField()
    userID=CharField()
    userName=CharField()
    timestamp=DateTimeField(default=datetime.datetime.now)

