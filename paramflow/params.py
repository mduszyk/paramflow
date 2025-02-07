import os
import argparse
from functools import reduce
from typing import List, Dict, Optional, Union, Final, Type

from paramflow.convert import convert_type
from paramflow.frozen import freeze, FrozenAttrDict
from paramflow.parser import TomlParser, YamlParser, JsonParser, EnvParser, ArgsParser, Parser


DEFAULT_ENV_PREFIX: Final[str] = 'P_'
DEFAULT_ARGS_PREFIX: Final[str] = ''
DEFAULT_DEFAULT_PROFILE: Final[str] = 'default'
DEFAULT_PROFILE_KEY: Final[str] = 'profile'

PARSER_MAP: Final[Dict[str, Type[Parser]]] = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
}


def load(**kwargs) -> FrozenAttrDict[str, any]:
    meta = {
        'path': None,
        'env_prefix': DEFAULT_ENV_PREFIX,
        'args_prefix': DEFAULT_ARGS_PREFIX,
        'profile_key': DEFAULT_PROFILE_KEY,
        'default_profile': DEFAULT_DEFAULT_PROFILE,
        'profile': DEFAULT_DEFAULT_PROFILE,
    }
    meta_env_parser = EnvParser(DEFAULT_ENV_PREFIX, meta, DEFAULT_DEFAULT_PROFILE)
    meta_args_parser = ArgsParser(DEFAULT_ARGS_PREFIX, DEFAULT_PROFILE_KEY, DEFAULT_DEFAULT_PROFILE, meta)
    layers = [meta, meta_env_parser(), meta_args_parser(), kwargs]
    meta = freeze(reduce(merge_layers, layers, {}))

    paths = meta.path
    if not isinstance(paths, list):
        paths = [paths]

    layers = []
    for path in paths:
        ext = path.split('.')[-1]
        parser_class = PARSER_MAP[ext]
        parser = parser_class(path)
        params = parser()
        if not meta.default_profile in params:
            params = {meta.default_profile: params}
        layers.append(params)

    if meta.env_prefix is not None:
        parser = EnvParser(meta.env_prefix, layers[0], meta.default_profile, profile=meta.profile)
        params = parser()
        if len(params) > 0:
            layers.append(params)

    if meta.args_prefix is not None:
        parser = ArgsParser(meta.args_prefix, meta.profile_key, meta.default_profile,
                            layers[0], profile=meta.profile)
        params = parser()
        if len(params) > 0:
            layers.append(params)

    params = merge(layers, meta.default_profile, meta.profile)

    return freeze(params)


def merge(layers: List[Dict[str, any]], default_profile: str, profile: str) -> Dict[str, any]:
    params = reduce(merge_layers, layers, {})
    profile_params = params[default_profile]
    active_profile_params = params.get(profile)
    merge_layers(profile_params, active_profile_params)
    return profile_params


def merge_layers(dst: dict, src: dict) -> dict:
    for key, src_value in src.items():
        if isinstance(src_value, dict) and isinstance(dst.get(key), dict):
            merge_layers(dst[key], src_value)
        elif isinstance(src_value, list) and isinstance(dst.get(key), list) and len(src_value) == len(dst[key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    merge_layers(dst_item[i], src_value[i])
                else:
                    dst_item[i] = convert_type(dst_item[i], src_value[i])
        else:
            # if key == '__source__':
            #     if not isinstance(dst[key], list):
            #         dst[key] = dst[key]
            #     dst[key].append(src_value)
            # else:
            dst[key] = convert_type(dst.get(key), src_value)
    return dst
