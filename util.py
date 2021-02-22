import re


# 全角符号转半角符号
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


# 跳过选择
def skip(s):
    if s[0] == '答': return True
    try:
        s = re.sub(r'[\*\+\-\/\=—\(*\)]*', '', s).replace(' ', '')
        # print(s)
        float(s)
        return True
    except ValueError:
        pass
    return False
