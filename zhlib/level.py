from wordfreq import word_frequency
import math

from . import db
from .util import find_hanzi, find_vocab


class Level:
    FREQ_FACTOR = 10**6

    @classmethod
    def hanzi_get_level(cls, hanzi):
        db_hanzi = db.Hanzi.get_or_none(hanzi=hanzi)
        if db_hanzi:
            return db_hanzi.junda

    def search_text(self, text):
        return {
            'hanzi': sorted(self.search_hanzi_iter(text), key=lambda x: x['sequence'] if x['sequence'] else math.inf),
            'vocab': sorted(self.search_vocab_iter(text), key=lambda x: -x['frequency'])
        }

    def search_hanzi_iter(self, text):
        for hanzi in find_hanzi(text):
            level = self.hanzi_get_level(hanzi)
            db_hanzi = db.Hanzi.get_or_none(hanzi=hanzi)
            if db_hanzi:
                hanzi_dict = db_hanzi.to_json()
            else:
                hanzi_dict = {
                    'hanzi': hanzi
                }

            yield {
                'sequence': level,
                **hanzi_dict
            }

    def search_vocab_iter(self, text):
        for vocab in find_vocab(text):
            db_vocab = db.Vocab.match(vocab)
            if db_vocab:
                vocab_dict = db_vocab[0].to_json()
            else:
                vocab_dict = {
                    'simplified': vocab
                }

            yield {
                'frequency': word_frequency(vocab, 'zh') * self.FREQ_FACTOR,
                **vocab_dict
            }
