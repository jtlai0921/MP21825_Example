import inout
import tower


class PARAM_no_recursion:
    DICT_BEGIN  = '[DictBegin]'
    DICT_END    = '[DictEnd]'
    DICT_NEXT   = '[DictNext]'
    DICT_KEY    = '[Key]'
    DICT_VALUE  = '[Value]'
    def __init__(self, *args, **kwargs):
        self.handle = inout.INOUT(*args, **kwargs)
    def read(self):
        result = {}
        next_tag = self.DICT_BEGIN
        while True:
            tag = self.handle.read()
            if not tag:
                return None
            elif tag != next_tag:
                if tag == self.DICT_END:
                    break
                raise ValueError('invalid tag %s' % str(tag))
            tag = self.handle.read()
            if tag != self.DICT_KEY:
                raise ValueError('get dict key error')
            key = self.handle.read()
            tag = self.handle.read()
            if tag != self.DICT_VALUE:
                raise ValueError('get dict value error')
            value = self.handle.read()
            result[key] = value
            next_tag = self.DICT_NEXT
        return result
    def write(self, param):
        next_tag = self.DICT_BEGIN
        for key, value in param.items():
            self.handle.write(next_tag)
            self.handle.write(self.DICT_KEY)
            self.handle.write(key)
            self.handle.write(self.DICT_VALUE)
            self.handle.write(value)
            next_tag = self.DICT_NEXT
        self.handle.write(self.DICT_END)
    def close(self):
        return self.handle.close()


class PARAM_no_limit:
    LIST_TAG       = '['
    NEXT_TAG       = ','
    END_TAG        = ';'
    DICT_TAG       = '{'
    DATA_TAG       = '\''
    def __init__(self, *args, **kwargs):
        self.handle = inout.INOUT(*args, **kwargs)
    def read_dict(self):
        result = {}
        while True:
            key = self.handle.read()
            value = self.read()
            result[key] = value
            tag = self.handle.read_tag()
            if tag == self.NEXT_TAG:
                continue
            if tag == self.END_TAG:
                break
            raise ValueError('invalid tag %s' % str(tag))
        return result
    def read_list(self):
        result = []
        while True:
            value = self.read()
            result.append(value)
            tag = self.handle.read_tag()
            if tag == self.NEXT_TAG:
                continue
            if tag == self.END_TAG:
                break
            raise ValueError('invalid tag %s' % str(tag))
        return result
    def read(self):
        tag = self.handle.read_tag()
        if not tag:
            return None
        elif tag == self.DICT_TAG:
            return self.read_dict()
        elif tag == self.LIST_TAG:
            return self.read_list()
        elif tag == self.DATA_TAG:
            return self.handle.read()
        raise ValueError('unknown tag %s' % tag)
    def write_dict(self, param):
        next_tag = self.DICT_TAG
        for key, value in param.items():
            self.handle.write_tag(next_tag)
            self.handle.write(key)
            self.write(value)
            next_tag = self.NEXT_TAG
        self.handle.write_tag(self.END_TAG)
    def write_list(self, param):
        next_tag = self.LIST_TAG
        for value in param:
            self.handle.write_tag(next_tag)
            self.write(value)
            next_tag = self.NEXT_TAG
        self.handle.write_tag(self.END_TAG)
    def write(self, param):
        if isinstance(param, dict):
            self.write_dict(param)
        elif isinstance(param, list):
            self.write_list(param)
        else:
            self.handle.write_tag(self.DATA_TAG)
            self.handle.write(param)
    def close(self):
        return self.handle.close()

class PARAM:
    LIST_TAG       = '['
    NEXT_TAG       = ','
    END_TAG        = ';'
    DICT_TAG       = '{'
    DATA_TAG       = '\''
    MAX_LEVEL      = 32
    MAX_ITEMS      = 16384
    def __init__(self, *args, **kwargs):
        self.handle = inout.INOUT(*args, **kwargs)
    def fix_level(self, level):
        if level < 0: level = 0
        if level > self.MAX_LEVEL:
            raise RecursionError('maximum recursion depth exceeded')
        return level
    def read_dict(self, level=0):
        level  = self.fix_level(level)
        result = {}
        nitems = 0
        while nitems < self.MAX_ITEMS:
            key = self.handle.read()
            value = self.read(level + 1)
            # print('read key:', key)
            # print('read value:', value)
            result[key] = value
            nitems += 1
            tag = self.handle.read_tag()
            if tag == self.NEXT_TAG:
                continue
            if tag == self.END_TAG:
                # print('read list:', result)
                return result
            raise ValueError('invalid tag %s' % str(tag))
        raise Exception('maximum items exceeded')
    def read_list(self, level=0):
        level  = self.fix_level(level)
        result = []
        nitems = 0
        while nitems < self.MAX_ITEMS:
            value = self.read(level + 1)
            # print('read value:', value)
            result.append(value)
            nitems += 1
            tag = self.handle.read_tag()
            if tag == self.NEXT_TAG:
                continue
            if tag == self.END_TAG:
                # print('read list:', result)
                return result
            raise ValueError('invalid tag %s' % str(tag))
        raise Exception('maximum items exceeded')
    def read_data(self):
        result = self.handle.read()
        # print('read data:', result)
        return result
    def read(self, level=0):
        level = self.fix_level(level)
        try:
            tag  = self.handle.read_tag()
        except:
            tag  = None
        if not tag:
            return None
        elif tag == self.DICT_TAG:
            return self.read_dict(level + 1)
        elif tag == self.LIST_TAG:
            return self.read_list(level + 1)
        elif tag == self.DATA_TAG:
            return self.read_data()
        raise ValueError('unknown tag %s' % tag)
    def write_dict(self, param):
        # print('write dict:', param)
        next_tag = self.DICT_TAG
        for key, value in param.items():
            # print('PARAM key-value:', type(key), type(value))
            self.handle.write_tag(next_tag)
            # print('PARAM write key:', type(key), key)
            self.handle.write(key)
            # print('PARAM write value:', type(value), value)
            self.write(value)
            next_tag = self.NEXT_TAG
        self.handle.write_tag(self.END_TAG)
    def write_list(self, param):
        # print('PARAM write list:', param)
        next_tag = self.LIST_TAG
        for value in param:
            self.handle.write_tag(next_tag)
            # print('PARAM write value:', type(value), value)
            self.write(value)
            next_tag = self.NEXT_TAG
        self.handle.write_tag(self.END_TAG)
    def write_data(self, param):
        self.handle.write_tag(self.DATA_TAG)
        # print('PARAM write data:', type(param), param)
        self.handle.write(param)
    def write(self, param):
        if isinstance(param, dict):
            self.write_dict(param)
        elif isinstance(param, list):
            self.write_list(param)
        else:
            self.write_data(param)
    def close(self):
        return self.handle.close()


def test_param():
    a = {'a': 1, 'b':2, 'c':3}
    p = PARAM(('localhost', 50007,))
    p.write(a)
    r = p.read()
    print(r)
    p.close()

if __name__ == '__main__':
    test_param()
