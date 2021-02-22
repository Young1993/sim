import jaro
import codecs
import json
import re
import os
from simhash import Simhash
import jieba
import copy


def main():
    # load data
    input_file = 'data/paper.json'
    output_file = codecs.open('data/question.txt', 'w', encoding='utf-8')
    f = open(input_file)
    content = f.read()
    res = json.loads(content)
    re_html = re.compile('</?\w+[^>]*>')
    question = []
    for i, block in enumerate(res['RECORDS']):
        o = json.loads(block['content'])
        # print(o['title'], type(o['title']))
        # print(re_html.sub('', block['content']['title']))
        tmp = {'index': i + 1, 'question_id': block['question_id'],
               'title': re_html.sub('', o['title']).replace('&nbsp;', '')}
        question.append(tmp)
        output_file.write(json.dumps(tmp, ensure_ascii=False) + '\n')
    print(f'question:{question}')

    # print(jaro.jaro_winkler_metric(u'一个数是700,另一个数比它少450,这个数是多少', u'一个数是800,另一个数比它少650,这个数是多少'))
    # print(jaro.jaro_winkler_metric(u'一个数是700,另一个数比它少450,这个数是多少', u'一个数是800,另一个数比它少450,这个数是多少'))


def strQ2B(ustring):
    ss = ""
    for s in ustring:
        rstring = ""
        for uchar in s:
            inside_code = ord(uchar)
            if inside_code == 12288:  # 全角空格直接转换
                inside_code = 32
            elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化
                inside_code -= 65248
            rstring += chr(inside_code)
        ss += rstring
    return ss


class Border():
    def __init__(self, test):
        self.boundary = []
        self.unsure = []
        self.d = {}
        self.test = test
        self.cut = [[word for word in jieba.cut(d['title'], cut_all=True)]
                    for d in self.test]

    def skip(self, s):
        if s[0] == '答': return True
        try:
            s = re.sub(r'[\*\+\-\/\=|—]*', '', s)
            # s = re.sub('\d*', '', s)
            # if not s: return True
            float(s)
            return True
        except ValueError:
            pass
        return

    # 第二轮，仔细比较待确定的题目
    def send_round(self):
        for block in self.unsure:
            if block['index'] not in self.d:
                block['raw'] = re.sub(r'^\d+\.', '', block['raw'])
                block['title'] = re.sub(r'^\d+\.', '', block['title'])
                l = len(block['raw'])
                p = jaro.jaro_winkler_metric(block['raw'], block['title'][:l])
                # distance = Simhash(jieba.cut(block['raw'], cut_all=True)).distance(Simhash(jieba.cut(block['title'][:l], cut_all=True)))
                print(f'\033[32;0m second round: {p}\033[0m')
                if p >= 0.9:
                    self.boundary.append(block)
                    self.unsure.remove(block)

    # 第一轮，获取确定的题目边界
    def first_round(self, target):
        # handle 图片窃取的内容
        # 标点符号的全角半角转换
        # 去除掉字符串内部的空格
        s = target['text']
        if self.skip(s): return
        s = strQ2B(s).replace(' ', '')  # re.sub(r'^\d+\.', '', target['text']).strip()
        s = re.sub(r'^\d+\.', '', s)
        m, index = 0, 0
        tmp, sim = [], []
        length = max(len(s), 9)

        for i, block in enumerate(self.test):
            p = jaro.jaro_winkler_metric(s, block['title'][:length + 1])
            # print(Simhash(s).distance(Simhash(block['title'][:length + 1 ])))
            tmp.append(p)
            sim.append(Simhash(jieba.cut(s, cut_all=True)).distance(Simhash(self.cut[i][:length + 1])))
            if p > m:
                index = i
                m = p

        # print(tmp)
        least_confident = 1 - m
        if least_confident >= 0.4:
            print('Wrong:', s)
            # print('Wrong:', s, m, self.test[index]['title'][:length + 1])
            # return False, m
        else:
            tmp.sort()
            min_sim = min(sim)
            a, b = tmp[-2:]
            if b - a > 0.08 and min_sim <= 15:
                print('picked:', s, m, self.test[index]['title'][:length + 1])
                # return self.test[index], m
                self.test[index]['raw'] = s
                self.test[index]['boundingBox'] = target['boundingBox']
                self.test[index]['probability'] = m
                self.test[index]['min_sim'] = min_sim
                if self.test[index]['index'] not in self.d:
                    self.d[self.test[index]['index']] = 1
                else:
                    self.d[self.test[index]['index']] = +1
                self.boundary.append(copy.deepcopy(self.test[index]))
                # else:
                #     print('picked:', s, m, self.test[index]['title'][:length + 1])
            else:
                print('need to confirm:', len(self.unsure), s, self.test[index]['title'][:length + 1])
                self.test[index]['raw'] = s
                self.test[index]['probability'] = m
                self.test[index]['min_sim'] = min_sim
                self.unsure.append(self.test[index])
                # return False, m


def test(order):
    input_file = 'data/question.txt'
    question = []
    with codecs.open(input_file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            tmp = json.loads(line)
            # 标点符号全角转半角、去空格
            tmp['title'] = strQ2B(tmp['title'].replace(" ", ""))
            # 去除题标
            tmp['title'] = re.sub(r'^\d+\.', '', tmp['title'])
            question.append(tmp)
    print(f'length of question:{len(question)}')

    test_file = 'paper/online-708-410000001106030-83501-' + order + '.txt'
    # test_file = 'paper/online-708-410000001106030-83501-1.txt'
    # test_file = 'paper/online-708-410000001106030-83501-2.txt'
    # test_file = 'paper/online-708-410000001106030-83501-3.txt'

    # for s in os.listdir('paper'):
    #     is_exsit = re.search(r'.txt', s)
    #     if is_exsit:
    #         print('*' * 100)
    #         print(s)
    #         test_file = 'paper/' + s
    border = Border(question)

    with codecs.open(test_file, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            block = json.loads(line)
            # print(block)
            for item in block['result']['regions']:
                for o in item['lines']:
                    # print(o['text'])
                    border.first_round(o)
    border.send_round()

    print(border.boundary, len(border.boundary))
    print('=' * 60)
    print(border.unsure, len(border.boundary))

    output_file = codecs.open('tmp/filter' + order + '.txt', 'w', encoding='utf-8')
    for o in border.boundary:
        output_file.write(json.dumps(o, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    # main()
    # input： 输入识别的文本，坐标值
    # 与试卷中的题目进行比较
    # output：题目的 question_id, 边界坐标
    order = '3'
    test(order)

    # print(jaro.jaro_winkler_metric('a', 'abb'))
    # print(jaro.jaro_winkler_metric('b', 'abb'))
    # print(jaro.jaro_metric('b', 'abb'))
    # print(jaro.jaro_winkler_metric('c', 'abbbb'))
    # print(jaro.jaro_winkler_metric('b', 'abbbbbb'))
    # print(jaro.jaro_winkler_metric('a', 'abbbbbbbbbb'))
    # print(jaro.jaro_winkler_metric('a', 'abbbbbbbbbbbbbbb'))
    # print(jaro.jaro_winkler_metric('a', 'abbbbbbbbbbbbbbbbbbbbbbbbbb'))
