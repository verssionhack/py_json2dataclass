import json as j
from typing import List


def type_name(value):
    return type(value).__name__


def list_struct_tree(value: list):
    tree = []
    for el in value:
        if type_name(el) == 'list':
            tree.append(list_struct_tree(el))
        elif type_name(el) == 'dict':
            tree.append(dict_struct_tree(el))
        else:
            tree.append(type_name(el))
    return tree

def dict_struct_tree(value: dict):
    tree = {}
    for k, v in value.items():
        tree[k] = {}
        if type_name(v) == 'dict':
            tree[k] = dict_struct_tree(v)
        elif type_name(v) == 'list':
            tree[k] = list_struct_tree(v)
        else:
            tree[k] = type_name(v)

    return tree

def is_list_all_eq(data: list):
    if len(data) == 0:
        return False
    l_struct_t = list_struct_tree(data)
    all_eq = True
    for i in range(1, len(l_struct_t)):
        if type_name(l_struct_t[0]) != type_name(l_struct_t[i]):
            all_eq = False
            break
    return all_eq

def parse_list(parent_dict: dict, field: str | None, data: list):
    if not 'name' in parent_dict:
        parent_dict['name'] = 'ParsedList'
    if not 'children_dataclasses' in parent_dict:
        parent_dict['children_dataclasses'] = []
    if not 'fields' in parent_dict:
        parent_dict['fields'] = {}

    if field == None:
        field = parent_dict['name'] + '_field'

    field = pascal2snake(field)


    if is_list_all_eq(data):
        if type_name(data[0]) == 'list':
            parent_dict['fields'][field] = f'List[{parse_list(parent_dict, field, data[0])}]'
        elif type_name(data[0]) == 'dict':
            parse_dict_res = {}
            for i in data:
                parse_dict_res.update(parse_dict(field, i))
            parent_dict['children_dataclasses'].append(parse_dict_res)
            parent_dict['fields'][field] = f'List[{snake2pascal(parse_dict_res["name"])}]'
        else:
            parent_dict['fields'][field] = f'List[{parse_unit(data[0])}]'
    else:
        for i in list_struct_tree(data):
            i_s = j.dumps(i, ensure_ascii=False)
            print(i_s)
            print(len(i_s))
        parent_dict['fields'][field] = 'list'

def parse_unit(data: str | int | float | bool):
    return type_name(data)


def parse_dict(name: str, data: dict):
    name = snake2pascal(name)
    children_dataclasses = []
    fields = {}

    ret = {'name': name, 'children_dataclasses': children_dataclasses, 'fields': fields}

    if len(data) == 0:
        return ret

    if all([i.isdigit() for i in data.keys()]) and is_list_all_eq(list(data.values())):
        values = list(data.values())
        return 'dict'

    for k, v in data.items():
        k = pascal2snake(k)
        v_type_name = type_name(v)

        if pascal2snake(k) in [pascal2snake(i['name']) for i in children_dataclasses]:
            continue

        if v_type_name == 'dict':
            parsed_dict = parse_dict(k, v)
            if type_name(parsed_dict) == 'str':
                fields[k] = 'dict'
            else:
                fields[k] = snake2pascal(k)
                children_dataclasses.append(parse_dict(k, v))
        elif v_type_name == 'list':
            parse_list(ret, k, v)
        else:
            fields[k] = v_type_name

    return ret


def parse(name: str, data: list | dict):
    ret = {}
    if type_name(data) == 'list':
        parse_list(ret, name, data)
    else:
        parsed_dict = parse_dict(name, data)
        if type_name(parsed_dict) == 'dict':
            ret.update(parsed_dict)
    return ret


def json2dataclass(data: dict):
    ret = []

    name = data['name']
    children_dataclasses = data['children_dataclasses']
    fields = data['fields']

    for children_dataclass in children_dataclasses:
        for i in json2dataclass(children_dataclass):
            if not i in ret:
                ret.append(i)

    class_header = \
f'''
@dataclass
class {name}:
'''
    class_body = ''
    for k, v in fields.items():
        class_body += f'    {k}: {v}\n'

    class_body_init = \
f'''
    def __init__(self, data: dict | None):
        if data == None:
            return None
'''

    for k, v in fields.items():
        class_body_init += f'        self.{k} = data.get("{k}")\n'


    gen = class_header + class_body + class_body_init

    if not gen in ret:
        ret.append(gen)
    return ret




def pascal2snake(value: str) -> str:
    if value.isupper():
        return value.lower()
    ret = ''
    for c in value:
        if 'A' <= c <= 'Z':
            if len(ret) > 0:
                ret += '_'
            ret += c.lower()
        else:
            ret += c
    return ret

def snake2pascal(value: str) -> str:
    ret = ''
    upper=True
    for c in value:
        if c == '_':
            upper = True
        else:
            if upper:
                upper = False
                ret += c.upper()
            else:
                ret += c
    return ret

def dict_key2snake_name(data: dict):
    if type(data) == type({}):
        keys = list(data.keys())
        for key in keys:
            dict_key2snake_name(data[key])
            if type(data[key]) == type([]):
                for i in range(len(data[key])):
                    dict_key2snake_name(data[key][i])

            data[pascal2snake(key)] = data.pop(key)
