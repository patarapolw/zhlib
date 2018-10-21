from zhlib.level import Level
from prettyprinter import pprint

if __name__ == '__main__':
    pprint(Level().search_text('''
# 注意

1. 中国人的姓和名
    - 中国人的姓和名在面，名在姓后。姓大多为一个音节，用一个汉子表示，两个音节的姓（复姓）也有一些。名字使用一个或两个汉子均可。用拼音拼写姓名时，姓与名之间有留一点间隔，姓和名的第一个字母有大写。
2. 你好/您好
    - 打招呼时的用语，适用于任何时间和场合。“您”是敬语，用于称呼长者，陌生人或不熟悉的人。
3. 冬生/小平
    - 直接用名字相称一般仅用于熟人之间。
4. 标点符号
    - 汉语的书写系统使用了很多标点符号，它们是书写系统中一个重要的组成部分。第一课使用的有以下几种：
        1. 感叹号“！”
            - 用于表示惊奇，奇怪，高兴，激动，打招呼，命令等语气。
        2. 逗号“，”
            - 用于意思相关的词，短语或句子之间的停顿。
        3. 句号“。”
            - 用于单独的词，短语或句子后的停顿。也可用于意思相关的几个句子之后，当意思完整时，最后一句使用句号。

# 练习
2. 辨音练习
    1. 佳节 嫁接 叠加 下列 铁甲
    2. 落后 篝火 搜索 筹措 收获 柔弱
    3. 开花 高喊 韩国 苦瓜 刻画 口感 毫克 滚开 顾客 跨国

# 附录
## 常用偏旁
- 笔画是组成汉子的最小的单位，例如：……等。单个的笔画不表示任何意思，但它们可以组合成表达某种意思的偏旁，是汉子中经常出现的组成部分，其中最常用的约有一百多个。
1. 偏胖有以下两类：
    1. 可单独使用的偏旁此类偏旁本身就是独体字，即可单独使用，也可用做合体字的组成部分。例如：
        - 独体字
        - 合体字
    2. 不能单独使用的偏旁：此类偏旁几乎全部是由独体字演化而来的，不能单独使用，只可用做合体字的组成部分。例如：
2. 偏旁的功能有以下三类：
    1. 表意：仅粗略地表示该字的意思与什么有关，开未详尽说明。例如：
        - “晚“中的”日“：表示与实践有关（按太阳的运行计算时间）
        - ”您“中的”心“：表示与感觉，心理有关（发自内心的尊重）
        - ”们“中的”亻“：表示与人的关
    2. 表音：最古老的象形字是利用自身的形体来表达字义，但当象形字发展到一定阶段后，古人开始意识到这种书与系统的弱点，即文字身体不表示发音，不便于认读，于是便开始利用一有的汉子作为新造汉子的部件，以表示该字如何发音。但是，在经过了数千年的发展演变之后，目前大多数表音偏旁的发音已与合体字的发音不一致或不安全一致，差异可能仅在于声母，云母或声调，也可能安全不一致。例如：
        - 偏旁
        - 合体字
    3. 构字部件：此类偏旁与汉子的意思及发音无关，用做部件仅为在形体上区别于其他汉字。
        - 另外，同一个偏旁，在一个汉子中可能起表意作用，而在另一个汉字中则可能起表音作用，或者仅作为构字部件。例如：
            - 门
    '''))
