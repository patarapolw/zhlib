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

    def to_dict(self):
        d = model_to_dict(self, backrefs=True, manytomany=True)
        d.pop('base_related')

        return d
    
    def to_json(self):
        d = model_to_dict(self)
        d.pop('base_related')
        
        return d

    class Meta:
        database = database


class Tag(BaseModel):
    name = pv.TextField(collation='NOCASE', unique=True)


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

    @property
    def more_vocabs(self):
        return Vocab.select().where(
            Vocab.simplified.contains(self.hanzi) | Vocab.traditional.contains(self.hanzi)
        )

    @property
    def more_sentences(self):
        return Sentence.select().where(Sentence.sentence.contains(self.hanzi))

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
            'compositions': self.compositions,
            'supercompositions': self.supercompositions,
            'variants': self.variants,
            'more_vocabs': self.more_vocabs,
            'more_sentences': self.more_sentences
        })

        return result

    def to_json(self):
        result = super(Hanzi, self).to_json()
        result.update({
            'vocabs': sort_vocab(set(v.simplified for v in
                                     Vocab.search(self.hanzi, Vocab.simplified, Vocab.traditional)), limit=10),
            'sentences': [s.sentence for s in
                          Sentence.select(Sentence.sentence).where(Sentence.sentence.contains(self.hanzi))][:10],
            'tags': [t.name for t in self.tags]
        })

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

    @property
    def more_sentences(self):
        query = Sentence.sentence.contains(self.simplified)
        if self.traditional:
            query = (query | Sentence.sentence.contains(self.simplified))

        return Sentence.select().where(query)

    @classmethod
    def search(cls, vocab, *fields):
        return cls.select(*fields).where(
            (cls.simplified == vocab) | (cls.traditional == vocab)
        )

    def to_dict(self):
        result = super(Vocab, self).to_dict()
        result.update({
            'more_sentences': self.more_sentences
        })

        return result

    def to_json(self):
        result = super(Vocab, self).to_json()
        result.update({
            'sentences': [s.sentence for s in self.more_sentences][:10],
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

    def to_json(self):
        result = super(Sentence, self).to_json()
        result.update({
            'vocab': sort_vocab(set(v.simplified for v in self.vocabs), limit=10),
            'tags': [t.name for t in self.tags]
        })

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
