from zhlib import db

db.database.create_tables([db.Tag, db.HanziTag, db.VocabTag, db.SentenceTag])
