from zhlib import zh
from prettyprinter import pprint
from wordfreq import word_frequency
import json

if __name__ == '__main__':
    d = dict()
    for i in range(1, 7):
        f = []
        tag_name = f'HSK_Level_{i}'
        for db_vocab in zh.Vocab.select().join(zh.VocabTag).join(zh.Tag).where(zh.Tag.name == tag_name):
            f.append(word_frequency(db_vocab.simplified, 'zh') * 10**6)

        d[tag_name] = {
            'max': max(f),
            'min': min(f)
        }

    with open('freq.json', 'w') as f:
        json.dump(d, f, indent=2 ,ensure_ascii=False)
