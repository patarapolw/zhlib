from wordfreq import word_frequency
import math

from . import db
from .util import find_hanzi, find_vocab


class Level:
    TIER_MIN = 1
    TIER_MAX = 6

    def __init__(self, text, jsonify=True):
        self.text = text
        self.jsonify = jsonify

    @property
    def hanzi(self):
        return sorted(HanziLevel(self.text, jsonify=self.jsonify),
                      key=lambda x: x[0] if x[0] else math.inf)

    @property
    def vocab(self):
        return sorted(VocabLevel(self.text, jsonify=self.jsonify),
                      key=lambda x: -x[0])

    @classmethod
    def normalize(cls, tier):
        tier = int(tier)
        if tier < cls.TIER_MIN:
            return cls.TIER_MIN
        elif tier > cls.TIER_MAX:
            return cls.TIER_MAX

        return tier


class HanziLevel:
    def __init__(self, text, jsonify=True):
        self.text = text
        self.jsonify = jsonify

    def __iter__(self):
        for hanzi in find_hanzi(self.text):
            level, tier = self.get_level(hanzi)
            db_hanzi = db.Hanzi.get_or_none(hanzi=hanzi)
            if db_hanzi:
                if self.jsonify:
                    yield level, tier, db_hanzi.to_json()
                else:
                    yield level, tier, db_hanzi
            else:
                yield level, tier, dict(hanzi=hanzi)

    def __len__(self):
        return len(find_hanzi(self.text))

    @classmethod
    def get_level(cls, hanzi):
        db_hanzi = db.Hanzi.get_or_none(hanzi=hanzi)
        if db_hanzi:
            level = db_hanzi.junda
        else:
            level = None

        if level:
            return level, Level.normalize(level // 400 + 1)

        return level, Level.TIER_MAX


class VocabLevel:
    FREQ_FACTOR = 10 ** 6

    def __init__(self, text, jsonify=True):
        self.text = text
        self.jsonify = jsonify

    def __iter__(self):
        for vocab in find_vocab(self.text):
            freq, tier = self.get_level(vocab)

            db_vocab = db.Vocab.match(vocab)
            if len(db_vocab) > 0:
                if self.jsonify:
                    yield freq, tier, db_vocab[0].to_json()
                else:
                    yield freq, tier, db_vocab[0]
            else:
               yield freq, tier, dict(simplified=vocab)

    def __len__(self):
        return len(find_vocab(self.text))

    @classmethod
    def get_level(cls, vocab):
        freq = word_frequency(vocab, 'zh') * cls.FREQ_FACTOR
        try:
            return freq, Level.normalize(7 - math.ceil(math.log10(freq) * 2))
        except ValueError:
            return freq, Level.TIER_MAX
