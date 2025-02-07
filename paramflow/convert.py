import json


CONVERSION_MAP = {
    int: {
        float: float,
        str: str,
    },
    float: {
        str: str,
    },
    bool: {
        str: str,
    },
    str: {
        bool: lambda s: s.lower() == 'true',
        int: int,
        float: float,
        dict: json.loads,
        list: json.loads,
    }
}

def convert_type(dst_value, src_value, key=''):
    dst_type = type(dst_value)
    src_type = type(src_value)
    if dst_type is src_type or dst_value is None:
        return src_value
    try:
        convert = CONVERSION_MAP[src_type][dst_type]
        return convert(src_value)
    except Exception as e:
        if key != '':
            key += ' '
        raise TypeError(f'unable to convert {key}{src_type} to {dst_type}') from e
