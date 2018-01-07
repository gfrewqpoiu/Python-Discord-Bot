from peewee import *
import datetime

db = SqliteDatabase('Quotes.db')

class Quote(Model):
    name = CharField(null = False, unique = True)
    text = TextField(null = True)
    imagelink = TextField(null = True)
    file = BlobField(null = True)
    times_used = IntegerField(default = 0)
    created_by = CharField()
    created_by_name = CharField()
    created_at = DateTimeField(default = datetime.datetime.now())

    class Meta:
        database = db # This model uses the "Quotes.db" database.

def createTextQuote(author, name: str, text: str):
    return Quote.create(name=name, text=text, created_by=author.id, created_by_name=author.name)

def createImageLinkQuote(author, name: str, link: str):
    return Quote.create(name=name, imagelink=link, created_by=author.id, created_by_name=author.name)

def createFileQuote(author, name: str, file):
    return Quote.create(name=name, file=file, created_by=author.id, created_by_name=author.name)

def createdb():
    db.create_tables([Quote], safe=True)
    return db