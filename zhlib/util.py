import regex
import jieba
from wordfreq import word_frequency

RE_IS_HAN = regex.compile(r'\p{IsHan}')


def is_han(s):
    return RE_IS_HAN.search(s)


def find_hanzi(s):
    return set(RE_IS_HAN.findall(s))


def find_vocab(s):
    return set(v for v in jieba.cut_for_search(s) if is_han(v))


def sort_vocab(v_list, limit=None):
    result = sorted(v_list, key=lambda x: -word_frequency(x, 'zh'))

    if limit:
        return result[:limit]

    return result
