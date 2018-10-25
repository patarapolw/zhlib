from ankix import ankix, db as a
from datetime import datetime
import peewee
from tqdm import tqdm

from .level import HanziLevel, VocabLevel


class Exporter:
    HANZI_A_FORMAT = '''
# {{hanzi}}
---
## {{pinyin}}

### {{meaning}}

- Junda: {{junda}}
- Heisig: {{heisig}}

#### Vocab
{{vocabs}}

#### Sentence
{{sentences}}
    '''
    VOCAB_A_FORMAT = '''
# {{simplified}}
---
## {{pinyin}}

### {{english}}

- Traditional: {{traditional}}
- Frequency: {{frequency}}

#### Sentence
{{sentences}}
    '''
    CSS = ''

    def __init__(self, filename):
        ankix.init(filename)
        self.db_model_hanzi = None
        self.db_model_vocab = None

    def search_text(self, text):
        with a.database.atomic():
            for f, t, hanzi in tqdm(HanziLevel(text, jsonify=False)):
                self.add_hanzi(hanzi)

            for f, t, vocab in tqdm(VocabLevel(text, jsonify=False)):
                self.add_vocab(vocab)

    def add_hanzi(self, hanzi):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        if not self.db_model_hanzi:
            self.db_model_hanzi  = a.Model.get_or_none(name='zhlib_hanzi')
            if self.db_model_vocab is None:
                self.db_model_hanzi = a.Model.add(
                    name='zhlib_hanzi',
                    templates=[
                        a.TemplateMaker(name='Forward', question='# Hanzi: {{hanzi}}',
                                        answer=self.HANZI_A_FORMAT),
                        a.TemplateMaker(name='Reverse', question='# Hanzi meaning: {{meaning}}',
                                        answer=self.HANZI_A_FORMAT)
                    ],
                    css=self.CSS
                )

        try:
            note_data = dict(hanzi)
            try:
                note_data.update({
                    'vocabs': '\n'.join(f'- {v}' for v in hanzi.get_vocabs(10)),
                    'sentences': '\n'.join(f'- {s}' for s in hanzi.get_sentences(10)),
                    'tags': None
                })
                tags = [str(t) for t in hanzi.tags]
            except AttributeError:
                tags = []

            a.Note.add(
                data=note_data,
                model=self.db_model_hanzi,
                card_to_decks={
                    'Forward': 'Chinese::Hanzi::zh->en',
                    'Reverse': 'Chinese::Hanzi::en->zh'
                },
                tags=(['zhlib', 'hanzi',
                       'tier{t}'.format(t=HanziLevel.get_level(note_data['hanzi'])[1]), timestamp] + tags)
            )
        except peewee.IntegrityError:
            pass

    def add_vocab(self, vocab):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        if not self.db_model_vocab:
            self.db_model_vocab = a.Model.get_or_none(name='zhlib_vocab')
            if self.db_model_vocab is None:
                self.db_model_vocab = a.Model.add(
                    name='zhlib_vocab',
                    templates=[
                        a.TemplateMaker(name='Forward', question='# Vocab: {{simplified}}',
                                        answer=self.VOCAB_A_FORMAT),
                        a.TemplateMaker(name='Reverse', question='# Vocab meaning: {{english}}',
                                        answer=self.VOCAB_A_FORMAT)
                    ],
                    css=self.CSS
                )
        try:
            note_data = dict(vocab)
            try:
                note_data.update({
                    'sentences': '\n'.join(f'- {s}' for s in vocab.get_sentences(10)),
                    'tags': None
                })
                tags = [str(t) for t in vocab.tags]
            except AttributeError:
                tags = []

            a.Note.add(
                data=note_data,
                model=self.db_model_vocab,
                card_to_decks={
                    'Forward': 'Chinese::Vocab::zh->en',
                    'Reverse': 'Chinese::Vocab::en->zh'
                },
                tags=(['zhlib', 'vocab',
                       'tier{t}'.format(t=VocabLevel.get_level(note_data['simplified'])[1]), timestamp] + tags)
            )
        except peewee.IntegrityError:
            pass
