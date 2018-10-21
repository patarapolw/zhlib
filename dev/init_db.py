from hanzilvlib.dictionary import HanziDict, VocabDict, SentenceDict
from tqdm import tqdm

from zhlib import db


def init():
    db.database.create_tables([
        db.Hanzi, db.Vocab, db.Sentence,
        db.VocabHanzi, db.SentenceHanzi, db.SentenceVocab
    ])


def fill_hanzi():
    for k, v in tqdm(HanziDict().entries.items()):
        db.Hanzi.get_or_create(
            hanzi=v['character'],
            pinyin=v['pinyin'],
            meaning=v['meaning'],
            heisig=int(v['heisig']) if v['heisig'] and v['heisig'] != '10000' else None,
            kanji=v['kanji']
        )


def fill_vocab():
    for k, v in tqdm(VocabDict().entries.items()):
        db.Vocab.get_or_create(
            simplified=v['simplified'],
            traditional=v['traditional'] if v['traditional'] != v['simplified'] else None,
            pinyin=v['pinyin'],
            english=v['english']
        )


def fill_sentence():
    for k, v in tqdm(SentenceDict().entries.items()):
        # print(v)
        db.Sentence.get_or_create(
            sentence=v['sentence'],
            pinyin=v['pinyin'],
            english=v['english'],
            order=int(v['order'])
        )


if __name__ == '__main__':
    # init()
    # fill_hanzi()
    # fill_vocab()
    fill_sentence()
