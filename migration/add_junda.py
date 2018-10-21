import peewee as pv
from playhouse.migrate import SqliteMigrator, migrate

from zhlib import db


if __name__ == '__main__':
    # migrator = SqliteMigrator(db.database)
    # migrate(
    #     migrator.add_column('hanzi', 'junda', pv.IntegerField(null=True, unique=True))
    # )

    with open('junda.txt') as f:
        for row in f:
            row = row.strip().split('\t')
            if row:
                junda = int(row[0])
                hanzi = row[1]

                db_hanzi = db.Hanzi.get_or_create(hanzi=hanzi)[0]
                db_hanzi.junda = junda
                db_hanzi.save()
