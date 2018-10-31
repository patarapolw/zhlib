import peewee as pv
from playhouse import signals
from playhouse.shortcuts import model_to_dict
from pathlib import Path
from cjkradlib import RadicalFinder

from .util import find_hanzi, find_vocab, sort_vocab

database = pv.SqliteDatabase(str(Path(__file__).with_name('dict.db')), pragmas={
    'query_only': 'ON'
})
radical_finder = RadicalFinder()


class BaseModel(signals.Model):
    base_related = pv.ForeignKeyField('self', backref='related', null=True)

    def __getitem__(self, item):
        return getattr(self, item)

    def to_dict(self):
        d = model_to_dict(self, backrefs=True, manytomany=True)
        d.pop('base_related')

        return d
    
    def to_json(self):
        d = model_to_dict(self)
        d.pop('base_related')
        
        return d

    def __iter__(self):
        return iter(self.to_json().items())

    class Meta:
        database = database


class Tag(BaseModel):
    name = pv.TextField(collation='NOCASE', unique=True)

    def __str__(self):
        return self.name


class Hanzi(BaseModel):
    hanzi = pv.TextField(unique=True)
    pinyin = pv.TextField(null=True)
    meaning = pv.TextField(null=True)
    heisig = pv.IntegerField(null=True)
    kanji = pv.TextField(null=True)
    junda = pv.IntegerField(null=True, unique=True)
    # vocabs
    # sentences
    tags = pv.ManyToManyField(Tag, backref='hanzis', on_delete='cascade')

    cache = dict()

    def __str__(self):
        return '{hanzi} {pinyin} {meaning}'.format(**dict(
            hanzi=self.hanzi,
            pinyin=('[{}]'.format(self.pinyin) if self.pinyin else ''),
            meaning=(self.meaning if self.meaning else '')
        ))

    @property
    def more_vocabs(self):
        return Vocab.select().where(
            Vocab.simplified.contains(self.hanzi) | Vocab.traditional.contains(self.hanzi)
        )

    def get_vocabs(self, limit=None):
        return sort_vocab(set(self.vocabs) | set(self.more_vocabs), limit=limit)

    @property
    def more_sentences(self):
        return Sentence.select().where(Sentence.sentence.contains(self.hanzi))

    def get_sentences(self, limit=None):
        i = 0
        for sentence in self.sentences:
            if not limit or (limit and i < limit):
                yield sentence
            i += 1

        for sentence in self.more_sentences:
            if not limit or (limit and i < limit):
                yield sentence
            i += 1

    @property
    def _rad_result(self):
        return self.cache\
            .setdefault(self.hanzi, dict())\
            .setdefault('rad_result', radical_finder.search(self.hanzi))

    @property
    def compositions(self):
        return getattr(self._rad_result, 'compositions', None)

    @property
    def supercompositions(self):
        return getattr(self._rad_result, 'supercompositions', None)

    @property
    def variants(self):
        return getattr(self._rad_result, 'variants', None)

    def to_dict(self):
        result = super(Hanzi, self).to_dict()
        result.update({
            'vocabs': self.get_vocabs(10),
            'sentences': list(self.get_sentences(10)),
            'compositions': self.compositions,
            'supercompositions': self.supercompositions,
            'variants': self.variants
        })

        return result

    def to_json(self):
        result = super(Hanzi, self).to_json()
        result.update({
            'vocabs': sort_vocab(Vocab.search(self.hanzi), limit=10),
            'sentences': [str(s) for s in
                          Sentence.select().where(Sentence.sentence.contains(self.hanzi))][:10],
            'tags': [t.name for t in self.tags]
        })
        result['vocabs'] = [str(v) for v in result['vocabs']]

        return result


HanziTag = Hanzi.tags.get_through_model()


class Vocab(BaseModel):
    simplified = pv.TextField()
    traditional = pv.TextField(null=True)
    pinyin = pv.TextField(null=True)
    english = pv.TextField(null=True)
    hanzis = pv.ManyToManyField(Hanzi, backref='vocabs', on_delete='cascade')
    # sentences
    tags = pv.ManyToManyField(Tag, backref='vocabs', on_delete='cascade')

    class Meta:
        indexes = (
            (('simplified', 'traditional', 'pinyin'), True),
        )

    def __str__(self):
        return '{simplified} {traditional} {pinyin} {english}'.format(**dict(
            simplified=self.simplified,
            traditional=(self.traditional if self.traditional else ''),
            pinyin=('[{}]'.format(self.pinyin) if self.pinyin else ''),
            english=(self.english if self.english else '')
        ))

    @property
    def more_sentences(self):
        query = Sentence.sentence.contains(self.simplified)
        if self.traditional:
            query = (query | Sentence.sentence.contains(self.simplified))

        return Sentence.select().where(query)

    def get_sentences(self, limit=None):
        i = 0
        for sentence in self.sentences:
            if not limit or (limit and i < limit):
                yield sentence
            i += 1

        for sentence in self.more_sentences:
            if not limit or (limit and i < limit):
                yield sentence
            i += 1

    @classmethod
    def search(cls, vocab):
        return cls.select().where(
            cls.simplified.contains(vocab) | cls.traditional.contains(vocab)
        )

    @classmethod
    def match(cls, vocab):
        return cls.select().where(
            (cls.simplified == vocab) | (cls.traditional == vocab)
        )

    def to_dict(self):
        result = super(Vocab, self).to_dict()
        result.update({
            'sentences': list(self.get_sentences(10))
        })

        return result

    def to_json(self):
        result = super(Vocab, self).to_json()
        result.update({
            'sentences': [str(s) for s in self.get_sentences(10)],
            'tags': [t.name for t in self.tags]
        })

        return result


VocabHanzi = Vocab.hanzis.get_through_model()
VocabTag = Vocab.tags.get_through_model()


@signals.post_save(sender=Vocab)
def vocab_post_save(model_class, instance, created):
    extra_hanzi = instance.traditional
    if not extra_hanzi:
        extra_hanzi = ''

    for hanzi in find_hanzi(instance.simplified + extra_hanzi):
        try:
            Hanzi.get_or_create(hanzi=hanzi)[0].vocabs.add(instance)
        except pv.IntegrityError:
            pass


class Sentence(BaseModel):
    sentence = pv.TextField()
    pinyin = pv.TextField(null=True)
    english = pv.TextField(null=True)
    hanzis = pv.ManyToManyField(Hanzi, backref='sentences', on_delete='cascade')
    vocabs = pv.ManyToManyField(Vocab, backref='sentences', on_delete='cascade')
    order = pv.IntegerField(null=True, unique=True)
    tags = pv.ManyToManyField(Tag, backref='sentences', on_delete='cascade')

    class Meta:
        indexes = (
            (('sentence', 'pinyin'), True),
        )

    def __str__(self):
        return '{sentence} {pinyin} {english}'.format(**dict(
            sentence=self.sentence,
            pinyin=('[{}]'.format(self.pinyin) if self.pinyin else ''),
            english=(self.english if self.english else '')
        ))

    def to_json(self):
        result = super(Sentence, self).to_json()
        result.update({
            'vocab': sort_vocab(set(v for v in self.vocabs), limit=10),
            'tags': [t.name for t in self.tags]
        })
        result['vocab'] = [str(v) for v in result['vocab']]

        return result


SentenceHanzi = Sentence.hanzis.get_through_model()
SentenceVocab = Sentence.vocabs.get_through_model()
SentenceTag = Sentence.tags.get_through_model()


@signals.post_save(sender=Sentence)
def sentence_post_save(model_class, instance, created):
    for hanzi in find_hanzi(instance.sentence):
        try:
            Hanzi.get_or_create(hanzi=hanzi)[0].vocabs.add(instance)
        except pv.IntegrityError:
            pass

    for vocab in find_vocab(instance.sentence):
        db_vocab = Vocab.select(Vocab.simplified, Vocab.traditional).where(
            (Vocab.simplified == vocab) | (Vocab.traditional == vocab)
        )

        if not db_vocab:
            Vocab.create(simplified=vocab).sentences.add(instance)
        else:
            try:
                db_vocab[0].sentences.add(instance)
            except pv.IntegrityError:
                pass


def search(s):
    sentences = ''
    if len(s) > 1:
        sentences = Sentence.select().where(Sentence.sentence == s)
    hanzis = ''
    if len(s) == 1:
        hanzis = Hanzi.select().where(Hanzi.hanzi == s)

    vocabs = Vocab.match(s)

    d = {
        'hanzi': hanzis,
        'vocab': vocabs,
        'sentences': sentences
    }

    to_pop = []
    for k, v in d.items():
        if len(v) == 0:
            to_pop.append(k)
        else:
            d[k] = [x.to_json() for x in v]

    for k in to_pop:
        d.pop(k)

    if len(d) == 1:
        v = tuple(d.values())[0]
        if len(v) == 1:
            return v[0]

    return d
