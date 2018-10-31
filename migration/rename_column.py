from playhouse.migrate import SqliteMigrator, migrate
from zhlib import zh

if __name__ == '__main__':
    migrator = SqliteMigrator(zh.database)
    migrate(
        migrator.rename_column('sentence', 'chinese', 'sentence')
    )
