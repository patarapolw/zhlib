from anki_export import ApkgReader
from bs4 import BeautifulSoup

from zhlib import zh

if __name__ == '__main__':
    with ApkgReader('/Users/patarapolw/Downloads/Hanyu_Shuiping_Kaoshi_HSK_all_5000_words_high_quality.apkg') as anki:
        for record in anki:
            db_vocab = zh.Vocab.get_or_create(
                simplified=record['Simplified'],
                traditional=record['Traditional'] if record['Traditional'] else None,
                defaults=dict(
                    pinyin=BeautifulSoup(record['Pinyin'], 'html.parser').text,
                    english=BeautifulSoup(record['English'], 'html.parser').text
                )
            )[0]

            for tag in record['tags'].strip().split(' '):
                zh.Tag.get_or_create(name=tag)[0].vocabs.add(db_vocab)
