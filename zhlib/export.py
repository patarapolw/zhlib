from ankix import Ankix, TemplateMaker
import math
from datetime import datetime
import peewee

from .level import Level


def text_to_ankix(
        text, ankix_filename,
        hanzi_range=(-math.inf, math.inf),
        vocab_range=(-math.inf, math.inf)
):
    d = Level().search_text(text, jsonify=False)
    a = Ankix(ankix_filename)
    timestamp = datetime.now().strftime('%Y-%m-%d')

    with a.database.atomic():
        db_models = a.get_models('zhlib_hanzi')
        if len(db_models) > 0:
            db_model = db_models[0]
        else:
            answer_format = '''
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
            db_model = a.add_model(
                model_name='zhlib_hanzi',
                templates=[
                    TemplateMaker(name='Forward', question='# {{hanzi}}', answer=answer_format),
                    TemplateMaker(name='Reverse', question='# {{meaning}}', answer=answer_format)
                ]
            )

        for f, t, hanzi in d['hanzi']:
            if f is None:
                f = math.inf

            if hanzi_range[0] <= f <= hanzi_range[1]:
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

                    a.add_note(
                        note_data=note_data,
                        model=db_model,
                        card_to_decks={
                            'Forward': 'Chinese::Hanzi::zh->en',
                            'Reverse': 'Chinese::Hanzi::en->zh'
                        },
                        tags=(['zhlib', f'lv{t}', timestamp] + tags)
                    )
                except peewee.IntegrityError:
                    pass

        db_models = a.get_models('zhlib_vocab')
        if len(db_models) > 0:
            db_model = db_models[0]
        else:
            answer_format = '''
# {{simplified}}
---
## {{pinyin}}

### {{english}}

- Traditional: {{traditional}}
- Frequency: {{frequency}}

#### Sentence
{{sentences}}
            '''
            db_model = a.add_model(
                model_name='zhlib_vocab',
                templates=[
                    TemplateMaker(name='Forward', question='# {{simplified}}', answer=answer_format),
                    TemplateMaker(name='Reverse', question='# {{english}}', answer=answer_format)
                ]
            )

        for f, t, vocab in d['vocab']:
            if vocab_range[0] <= f <= vocab_range[1]:
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

                    a.add_note(
                        note_data=note_data,
                        model=db_model,
                        card_to_decks={
                            'Forward': 'Chinese::Vocab::zh->en',
                            'Reverse': 'Chinese::Vocab::en->zh'
                        },
                        tags=(['zhlib', f'lv{t}', timestamp] + tags)
                    )
                except peewee.IntegrityError:
                    pass
