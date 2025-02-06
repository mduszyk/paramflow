from functools import reduce
from typing import List

from frozen import FrozenAttrDict
from parser import TomlParser, YamlParser, JsonParser, EnvParser, ArgsParser


parser_map = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
}

def load_params(paths, env_prefix=None, args_prefix=None, profile_key='params_profile', **kwargs):
    if not isinstance(paths, list):
        paths = [paths]
    full_params_list = []
    for path in paths:
        ext = path.split('.')[-1]
        parser_class = parser_map[ext]
        parser = parser_class(path)
        full_params_list.append(parser())
    params_list = []
    if env_prefix is not None:
        parser = EnvParser(env_prefix)
        params_list.append(parser(full_params_list[0]))
    if args_prefix is not None:
        parser = ArgsParser(args_prefix, profile_key)
        params_list.append(parser(full_params_list[0]))
    return merge_params(full_params_list, params_list, profile_key=profile_key, **kwargs)


def merge_params(full_params_list: List[dict], params_list: List[dict],
                 profile: str=None, profile_key: str='params_profile', default_profile='default'):

    full_params = reduce(update_leaves, full_params_list)
    params = reduce(update_leaves, params_list)

    profile_params = full_params.get(default_profile)
    if profile_params is None:
        # profiles not in use
        profile_params = full_params
    else:
        if profile is None:
            profile = params.get(profile_key)
        if profile is not None:
            update_leaves(profile_params, full_params[profile])

    update_leaves(profile_params, params)

    return freeze(profile_params)


def update_leaves(dst: dict, src: dict):
    for key, src_value in src.items():
        if isinstance(src_value, dict) and isinstance(dst.get(key), dict):
            update_leaves(src_value, dst[key])
        elif isinstance(src_value, list) and isinstance(dst.get(key), list) and len(src_value) == len(dst[key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    update_leaves(src_value[i], dst_item[i])
                else:
                    dst_item[i] = src_value[i]
        else:
            dst[key] = src_value
    return dst


def freeze(params: dict):
    # TODO recursively freeze all dicts and lists
    return FrozenAttrDict(params)
