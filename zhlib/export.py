from datetime import datetime
import peewee
import simplesrs as srs
import mistune
import logging
from ankisync.anki import Anki
from ankisync.apkg import Apkg
from ankisync.presets import get_wanki_min_dconf

from .level import HanziLevel, VocabLevel
from .util import progress_bar
from . import zh

markdown = mistune.Markdown()


class AnkiExporter:
    MODEL_HANZI = 'zhlib_hanzi'
    MODEL_VOCAB = 'zhlib_vocab'
    DECK_CONFIG = 'wanki.min'

    HANZI_A_FORMAT = markdown('''
# {{hanzi}}
---
## {{pinyin}}

### {{meaning}}

Junda: {{junda}}

Heisig: {{heisig}}

#### Vocab
{{vocabs}}

#### Sentence
{{sentences}}
    ''')
    VOCAB_A_FORMAT = markdown('''
# {{simplified}}
---
## {{pinyin}}

### {{english}}

Traditional: {{traditional}}

Frequency: {{frequency}}

#### Sentence
{{sentences}}
    ''')

    def __init__(self, apkg_filename=None):
        if apkg_filename:
            self.anki = Apkg(apkg_filename, disallow_unsafe=None)
            self.anki.init(
                first_model=self._build_model_vocab(),
                first_deck='Chinese',
                first_dconf=get_wanki_min_dconf()
            )
        else:
            self.anki = Anki(disallow_unsafe=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def close(self):
        return getattr(self.anki, 'close', lambda: None)()

    def search_text(self, text):
        hanzis = []
        for f, t, hanzi in progress_bar(HanziLevel(text, jsonify=False), desc='Extracting Hanzi'):
            hanzis.append(hanzi)
        self.add_hanzis(progress_bar(hanzis, desc='Adding Hanzi'))

        vocabs = []
        for f, t, vocab in progress_bar(VocabLevel(text, jsonify=False), desc='Extracting vocab'):
            vocabs.append(vocab)
        self.add_vocabs(progress_bar(vocabs, desc='Adding vocab'))

    def _build_model_hanzi(self):
        field_names = [
            'hanzi',    # The two fields of the question side must be firsts in order.
            'meaning',  # This too.
            'pinyin',
            'heisig',
            'kanji',
            'junda',
            'vocabs',
            'sentences',
            'note'
        ]

        return dict(
            name=self.MODEL_HANZI,
            fields=field_names,
            templates={
                'Forward': (markdown('# Hanzi: {{hanzi}}'), self.HANZI_A_FORMAT),
                'Reverse': (markdown('# Hanzi meaning: {{meaning}}'), self.HANZI_A_FORMAT)
            }
        )

    def add_model_hanzi(self):
        self.anki.add_model(**self._build_model_hanzi())

    def add_hanzis(self, hanzis):
        if self.MODEL_HANZI not in self.anki.model_names():
            self.add_model_hanzi()

        note_ids = self.anki.upsert_notes([self._build_hanzi_note(hanzi) for hanzi in hanzis])

        for i in range(1, 7):
            self.change_deck('Hanzi', i, note_ids)

    def _build_hanzi_note(self, hanzi):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        note_data_defaults = dict(hanzi)
        h_key = note_data_defaults.pop('hanzi')

        try:
            note_data_defaults.update({
                'vocabs': markdown('\n'.join(f'- {v}' for v in hanzi.get_vocabs(10))),
                'sentences': markdown('\n'.join(f'- {s}' for s in hanzi.get_sentences(10)))
            })
            note_data_defaults.pop('tags')
            tags = [str(t) for t in hanzi.tags]
        except AttributeError:
            tags = []

        return {
            'deckId': 1,
            'modelName': self.MODEL_HANZI,
            'fields': {
                'hanzi': h_key,
                'defaults': dict((k, str(v)) for k, v in note_data_defaults.items() if v is not None)
            },
            'tags': ['zhlib', 'hanzi',
                     'tier{t}'.format(t=HanziLevel.get_level(h_key)[1]), timestamp] + tags
        }

    def _build_model_vocab(self):
        field_names = [
            'simplified',   # The two fields of the question side must be firsts in order.
            'english',      # This too.
            'frequency',
            'traditional',
            'pinyin',
            'sentences',
            'note'
        ]

        return dict(
            name=self.MODEL_VOCAB,
            fields=field_names,
            templates={
                'Forward': (markdown('# Vocab: {{simplified}}'), self.VOCAB_A_FORMAT),
                'Reverse': (markdown('# Vocab meaning: {{english}}'), self.VOCAB_A_FORMAT)
            }
        )

    def add_model_vocab(self):
        self.anki.add_model(**self._build_model_vocab())

    def add_vocabs(self, vocabs):
        if self.MODEL_VOCAB not in self.anki.model_names():
            self.add_model_vocab()

        note_ids = self.anki.upsert_notes([self._build_vocab_note(vocab) for vocab in vocabs])

        for i in range(1, 7):
            self.change_deck_hsk(i, note_ids)
            self.change_deck('Vocab', i, note_ids)

    def _build_vocab_note(self, vocab):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        note_data_defaults = dict(vocab)
        simplified = note_data_defaults.pop('simplified')

        f, t = VocabLevel.get_level(simplified)
        note_data_defaults['frequency'] = str(f)

        try:
            note_data_defaults.update({
                'sentences': markdown('\n'.join(f'- {s}' for s in vocab.get_sentences(10)))
            })
            note_data_defaults.pop('tags')
            tags = [str(t) for t in vocab.tags]
        except AttributeError:
            tags = []

        return {
            'deckId': 1,
            'modelName': self.MODEL_VOCAB,
            'fields': {
                'simplified': simplified,
                'defaults': dict((k, str(v)) for k, v in note_data_defaults.items() if v is not None)
            },
            'tags': ['zhlib', 'vocab',
                     'tier{t}'.format(t=t), timestamp] + tags
        }

    def change_deck(self, type_, tier, note_ids):
        card_forward = set()
        card_reverse = set()
        for note_id in note_ids:
            search_result = self.anki.search_notes({'_nid': note_id})
            tags = search_result[0]['_tags']
            if type_.lower() in tags and f'tier{tier}' in tags and all('HSK' not in t for t in tags):
                card_forward.add(self.anki.note_to_cards(note_id)['Forward'])
                card_reverse.add(self.anki.note_to_cards(note_id)['Reverse'])

        try:
            dconf_id = self.anki.deck_config_names_and_ids()[self.DECK_CONFIG]
        except KeyError:
            dconf_id = self.anki.save_deck_config(get_wanki_min_dconf())

        self.anki.change_deck(card_forward, f'Chinese::{type_}::tier{tier}::zh->en', dconf=dconf_id)
        self.anki.change_deck(card_reverse, f'Chinese::{type_}::tier{tier}::en->zh', dconf=dconf_id)

    def change_deck_hsk(self, lv, note_ids):
        type_ = 'Vocab'

        card_forward = set()
        card_reverse = set()
        for note_id in note_ids:
            search_result = self.anki.search_notes({'_nid': note_id})
            tags = search_result[0]['_tags']
            if type_.lower() in tags and f'HSK_Level_{lv}' in tags:
                card_forward.add(self.anki.note_to_cards(note_id)['Forward'])
                card_reverse.add(self.anki.note_to_cards(note_id)['Reverse'])

        try:
            dconf_id = self.anki.deck_config_names_and_ids()[self.DECK_CONFIG]
        except KeyError:
            dconf_id = self.anki.save_deck_config(get_wanki_min_dconf())

        self.anki.change_deck(card_forward, f'Chinese::{type_}::HSK{lv}::zh->en', dconf=dconf_id)
        self.anki.change_deck(card_reverse, f'Chinese::{type_}::HSK{lv}::en->zh', dconf=dconf_id)


class SimpleSrsExporter:
    def __init__(self, filename):
        srs.init(filename)

    @classmethod
    def add_hanzi(cls, hanzi):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        try:
            db_hanzi = zh.Hanzi.get_or_none(hanzi=hanzi)
            info = dict()
            tags = []
            if db_hanzi:
                tags = [str(t) for t in db_hanzi.tags]
                info = db_hanzi.to_json()
                srs.Card.add(
                    item='Hanzi meaning: {}'.format(db_hanzi.meaning),
                    info=info,
                    tags=(['zhlib', 'hanzi', 'en->zh',
                           'tier{t}'.format(t=HanziLevel.get_level(hanzi)[1]),
                           timestamp] + tags)
                )

            srs.Card.add(
                item='Hanzi: {}'.format(hanzi),
                info=info,
                tags=(['zhlib', 'hanzi', 'zh->en',
                       'tier{t}'.format(t=HanziLevel.get_level(hanzi)[1]),
                       timestamp] + tags)
            )
        except peewee.IntegrityError:
            logging.error('%s not added', hanzi)

    @classmethod
    def add_vocab(cls, vocab):
        timestamp = datetime.now().strftime('%Y-%m-%d')

        try:
            db_vocabs = zh.Vocab.match(vocab)
            info = dict()
            tags = list()
            if len(db_vocabs) > 0:
                tags = [str(t) for t in db_vocabs[0].tags]
                info = db_vocabs[0].to_json()
                srs.Card.add(
                    item='Vocab meaning: {}'.format(db_vocabs[0].english),
                    info=info,
                    tags=(['zhlib', 'vocab', 'en->zh',
                           'tier{t}'.format(t=HanziLevel.get_level(vocab)[1]),
                           timestamp] + tags)
                )

            srs.Card.add(
                item='Vocab: {}'.format(vocab),
                info=info,
                tags=(['zhlib', 'vocab', 'zh->en',
                       'tier{t}'.format(t=HanziLevel.get_level(vocab)[1]),
                       timestamp] + tags)
            )
        except peewee.IntegrityError:
            logging.error('%s not added', vocab)
