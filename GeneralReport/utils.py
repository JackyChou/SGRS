#coding:utf-8

def replace_invalid_quote(input_str):
    '''replace single quote,chinese single quote,chinese double quote'''
    input_str = input_str.replace(u"‘","'")
    input_str = input_str.replace(u"’","'")
    input_str = input_str.replace(u"”",'"')
    input_str = input_str.replace(u"“",'"')
    return input_str
