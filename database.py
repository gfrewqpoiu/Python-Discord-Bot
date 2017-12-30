from peewee import *

db = SqliteDatabase('Quotes.db')

class Quote(Model):
    name = CharField(null = False)
    text = TextField(null = False)
    times_used = IntegerField(default = 0)

    class Meta:
        database = db # This model uses the "people.db" database.


def createdb():
    db.create_tables([Quote], safe=True)
    return db