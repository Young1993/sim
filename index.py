'''
test for similarity
'''
import jaro
# from simhash import Simhash
# import jieba
import codecs
import json
import re
from sim import util
import numpy as np
import copy


class Similarity():
    def __init__(self):
        self.knowledge_list = [] # 知识点列表
        self.gold_standard = []  # 试卷中的题目列表
        self.slice_test = []  # 待确定的题目

    def load_jyeoo_data(self):
        f = open('../jyeoo/data/primary.json')
        content = f.read()
        content = json.loads(content)
        for i in range(len(content)):
            _, name = content[i].split('：')
            self.knowledge_list.append(name)
        print('finish loaded')

    # 加载试卷
    def load_gold_standard(self, name='data/question.txt'):
        with codecs.open(name, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                tmp = json.loads(line)
                # 标点符号全角转半角、去空格
                tmp['title'] = util.strQ2B(tmp['title'].replace(" ", ""))
                # 去除题标
                # tmp['title'] = re.sub(r'^\d+\.', '', tmp['title'])
                self.gold_standard.append(tmp)
        print(f'length of gold standard:{len(self.gold_standard)}')

    # 加载切片试题
    def load_slice_test(self, name='paper/online-708-410000001106030-83501-0.txt'):
        with codecs.open(name, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                block = json.loads(line)
                for item in block['result']['regions'][1:-1]:
                    for o in item['lines']:
                        if util.skip(o['text']): continue  # filter nosies
                        o['text'] = util.strQ2B(o['text'].replace(" ", ""))
                        self.slice_test.append(o)

    def convert_to_vector(self, s1, s2):
        l = len(s1)
        s2 = s2[: l + 2] if l < 10 else s2[: l + 4]
        word = list(set([o for o in s1] + [o for o in s2]))
        total = len(word)
        word_vector1 = np.zeros(total)
        word_vector2 = np.zeros(total)

        for i in range(total):
            for o in s1:
                if o == word[i]: word_vector1[i] += 1
            for o in s2:
                if o == word[i]: word_vector2[i] += 1
        return word_vector1, word_vector2

    # jaccard 相似度
    def jaccard(self, s1='', s2='', mode='strict'):
        if mode == 'strict':
            s1 = re.sub(r'^\d+\.', '', s1)
            s2 = re.sub(r'^\d+\.', '', s2)
            l1 = len(s1)
            s2 = s2[: l1 + 1]
            l2 = len(s2)
        else:
            l1 = len(s1)
            s2 = s2[: l1 + 2] if l1 < 10 else s2[: l1 + 4]
            l2 = len(s2)
        temp = 0
        for o in s1:
            if o in s2:
                temp += 1
        total = l1 + l2 - temp
        return float(temp / total)

    # 余弦相似度
    def cosine_similarity(self, s1='', s2=''):
        return float(np.dot(s1, s2) / (np.linalg.norm(s1) * np.linalg.norm(s2)))

    # filter slice
    def filter_slice(self, method='cosine'):
        output_file = codecs.open('test/' + method + '.txt', 'w', encoding='utf-8')
        for input1 in self.slice_test:
            # output_file = codecs.open('test/t' + str(index) + '.json', 'w', encoding='utf-8')
            # print(index, input1['text'])
            # compare similarity
            tmp, max_p, index = [], 0, 0
            for i, block in enumerate(self.gold_standard):
                if not block['title']: continue

                if method == 'cosine':
                    s1, s2 = self.convert_to_vector(input1['text'], block['title'])
                    p = self.cosine_similarity(s1, s2)
                elif method == 'jaccard':
                    p = self.jaccard(input1['text'], block['title'])

                print(f"probability:{p}, title: {block['title']}")

                tmp.append(p)
                if p > max_p:
                    max_p, index = p, i

            if max_p >= 0.8:
                question_copy = copy.deepcopy(self.gold_standard[index])
                question_copy['probability'] = max_p
                question_copy['slice_text'] = input1['text']

                output_file.write(json.dumps(question_copy, indent=2, ensure_ascii=False) + '\n')
            elif 0.8 > max_p >= 0.6:
                tmp.sort()
                a, b = tmp[-2:]
                print(input1['text'], b, a)
                if b - a >= 0.1:
                    question_copy = copy.deepcopy(self.gold_standard[index])
                    question_copy['probability'] = max_p
                    question_copy['slice_text'] = input1['text']
                    output_file.write(json.dumps(question_copy, indent=2, ensure_ascii=False) + '\n')


def main():
    s = Similarity()
    s.load_jyeoo_data()
    input = '周长的认识'
    arr = []
    for item in s.knowledge_list:
        p = jaro.jaro_winkler_metric(input, item)
        arr.append(p)
        # print()
    list = np.array(arr)
    ind = np.argpartition(list, -6)[-6:]
    for o in ind:
        print(s.knowledge_list[o], arr[o])


if __name__ == '__main__':
    main()
