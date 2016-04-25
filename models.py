import peewee


db = peewee.SqliteDatabase('lhc.db')


class Entry(peewee.Model):

    entry_date = peewee.DateField()
    value = peewee.DecimalField()
    account = peewee.CharField()
    tags = peewee.CharField
    description = peewee.TextField()

    class Meta:
        database = db


db.create_tables([Entry, ], safe=True)
