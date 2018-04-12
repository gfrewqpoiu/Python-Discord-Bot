from peewee import *
from playhouse.pool import *
import datetime

db = PooledSqliteDatabase('Quotes.db')

class Quote(Model):
    name = CharField(null = False, unique = True)
    text = TextField(null = True)
    link = TextField(null = True)
    times_used = IntegerField(default = 0)
    created_by = CharField()
    created_by_name = CharField()
    created_at = DateTimeField(default = datetime.datetime.now())

    class Meta:
        database = db # This model uses the "Quotes.db" database.

def createTextQuote(author, name: str, text: str):
    return Quote.create(name=name, text=text, created_by=author.id, created_by_name=author.name)

def createLinkQuote(author, name: str, link: str):
    return Quote.create(name=name, link=link, created_by=author.id, created_by_name=author.name)

def createdb():
    db.create_tables([Quote], safe=True)
    return db