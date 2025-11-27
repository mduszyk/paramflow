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
        tuple: lambda s: (s,)
    }
}

def convert_type(dst_value, src_value, path=''):
    dst_type = type(dst_value)
    src_type = type(src_value)
    if dst_type is src_type or dst_value is None:
        return src_value
    try:
        convert = CONVERSION_MAP[src_type][dst_type]
        return convert(src_value)
    except Exception as e:
        if path != '':
            path += ' '
        raise TypeError(f'unable to convert {path}{src_type} to {dst_type}') from e


def infer_type(value: str):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
