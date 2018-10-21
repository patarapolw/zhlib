from playhouse.migrate import SqliteMigrator, migrate
from zhlib import db

if __name__ == '__main__':
    migrator = SqliteMigrator(db.database)
    migrate(
        migrator.drop_index('sentence', 'sentence_chinese'),
        migrator.add_index('sentence', ('sentence', 'pinyin'), True)
    )
