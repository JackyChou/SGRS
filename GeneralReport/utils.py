#coding:utf-8

def replace_invalid_quote(input_str):
    '''replace single quote,chinese single quote,chinese double quote'''
    input_str = input_str.replace(u"‘","'")
    input_str = input_str.replace(u"’","'")
    input_str = input_str.replace(u"”",'"')
    input_str = input_str.replace(u"“",'"')
    return input_str

class ObjectDict(dict):
    """
    Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

