import os
import argparse
from functools import reduce
from typing import List, Dict, Optional, Union, Final, Type

from paramflow.convert import convert_type
from paramflow.frozen import freeze, FrozenAttrDict
from paramflow.parser import TomlParser, YamlParser, JsonParser, EnvParser, ArgsParser, Parser


# defaults
ENV_PREFIX: Final[str] = 'P_'
ARGS_PREFIX: Final[str] = ''
DEFAULT_PROFILE: Final[str] = 'default'
PROFILE_KEY: Final[str] = 'profile'

PARSER_MAP: Final[Dict[str, Type[Parser]]] = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
}


def load(path: Optional[Union[str, List[str]]] = None,
         env_prefix: str = ENV_PREFIX,
         args_prefix: str = ARGS_PREFIX,
         profile_key: str = PROFILE_KEY,
         default_profile: str = DEFAULT_PROFILE,
         profile: Optional[str] = DEFAULT_PROFILE) -> FrozenAttrDict[str, any]:

    meta = {
        'path': path,
        'env_prefix': env_prefix,
        'args_prefix': args_prefix,
        'profile_key': profile_key,
        'default_profile': default_profile,
        profile_key: profile,
    }
    meta_env_parser = EnvParser(ENV_PREFIX, meta, DEFAULT_PROFILE)
    meta_args_parser = ArgsParser(ARGS_PREFIX, PROFILE_KEY, DEFAULT_PROFILE, meta)
    layers = [meta, meta_env_parser(), meta_args_parser()]
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
    if '__source__' in params:
        profile_params['__source__'] = params['__source__']
    if profile != default_profile:
        active_profile_params = params.get(profile)
        merge_layers(profile_params, active_profile_params)
    return profile_params


def merge_layers(dst: dict, src: dict) -> dict:
    for src_key, src_value in src.items():
        if src_key == '__source__':
            if not src_key in dst:
                dst[src_key] = []
            dst[src_key].extend(src_value)
        elif isinstance(src_value, dict) and isinstance(dst.get(src_key), dict):
            merge_layers(dst[src_key], src_value)
        elif isinstance(src_value, list) and isinstance(dst.get(src_key), list) and len(src_value) == len(dst[src_key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    merge_layers(dst_item[i], src_value[i])
                else:
                    dst_item[i] = convert_type(dst_item[i], src_value[i])
        else:
            dst[src_key] = convert_type(dst.get(src_key), src_value)
    return dst
