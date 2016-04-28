import datetime
import json
import peewee
from playhouse.shortcuts import model_to_dict

db = peewee.SqliteDatabase('lhc.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db

    def to_dict(self, json_safe=True, datefield_format='%Y-%m-%d'):
        dict_model = model_to_dict(self)

        if json_safe:  # make returned dict serializable by json library
            for key, value in dict_model.items():
                if isinstance(value, datetime.date):
                    new_value = value.strftime(datefield_format)
                    dict_model[key] = new_value

        return dict_model


class Entry(BaseModel):

    entry_date = peewee.DateField()
    value = peewee.DecimalField()
    account = peewee.CharField()
    tags = peewee.CharField
    description = peewee.TextField()


db.create_tables([Entry, ], safe=True)
