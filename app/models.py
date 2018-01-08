import datetime
import peewee
from playhouse.shortcuts import model_to_dict
from playhouse.signals import Model, post_save

db = peewee.SqliteDatabase('lhc.db')


class BaseModel(Model):

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
    tags = peewee.CharField()
    description = peewee.TextField()


@post_save(sender=Entry)
def on_save_entry_handler(model_class, instance, created):
    entry_year = datetime.datetime.strptime(
        instance.entry_date, '%Y-%m-%d').year
    report_file = 'templates/lhc_{}.html'.format(entry_year)
    with open('lhc_report_template.html', 'r') as template:
        report_template = template.read()

    with open(report_file, 'w') as report:
        formatted_entries = []
        entries = Entry.select().where(Entry.entry_date.year == entry_year)

        for entry in entries:
            formatted_entry = u'{entry_date}\t{value:.2f}\t\t{account},{tags}|#{id} - {description}'.format(
                entry_date=entry.entry_date,
                value=entry.value,
                account=entry.account,
                tags=entry.tags,
                id=entry.id,
                description=entry.description
            )
            formatted_entries.append(formatted_entry)

        report.write(
            report_template.replace('[[entries]]', '\n'.join(formatted_entries))
        )

if not Entry.table_exists():
    db.create_tables([Entry, ], safe=True)
