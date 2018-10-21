from playhouse.migrate import SqliteMigrator, migrate
from zhlib import db

if __name__ == '__main__':
    migrator = SqliteMigrator(db.database)
    migrate(
        migrator.rename_column('sentence', 'chinese', 'sentence')
    )
