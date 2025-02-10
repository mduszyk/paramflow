import argparse
import os
import sys
from functools import reduce
from typing import List, Dict, Optional, Union, Final, Type

from paramflow.convert import convert_type
from paramflow.frozen import freeze, FrozenAttrDict
from paramflow.parser import PARSER_MAP, EnvParser, ArgsParser, DotEnvParser

# defaults
ENV_PREFIX: Final[str] = 'P_'
ARGS_PREFIX: Final[str] = ''
DEFAULT_PROFILE: Final[str] = 'default'
PROFILE_KEY: Final[str] = 'profile'


def load(file: Optional[Union[str, List[str]]] = None,
         env_prefix: str = ENV_PREFIX,
         args_prefix: str = ARGS_PREFIX,
         profile_key: str = PROFILE_KEY,
         default_profile: str = DEFAULT_PROFILE,
         profile: Optional[str] = DEFAULT_PROFILE,
         dot_env_file: Optional[str] = None) -> FrozenAttrDict[str, any]:
    """
    Load parameters.
    :param file: file or multiple files to load parameters from
    :param env_prefix: prefix for env vars that are used to overwrite params
    :param args_prefix: prefix for command-line arguments
    :param profile_key: parameter name for the profile
    :param default_profile: default profile
    :param profile: profile to activate
    :param dot_env_file: file containing environment variables usually '.env'
    :return:
    """

    meta = {
        'file': file,
        'env_prefix': env_prefix,
        'args_prefix': args_prefix,
        'profile_key': profile_key,
        'default_profile': default_profile,
        profile_key: profile,
        'dot_env_file': dot_env_file,
    }
    meta_env_parser = EnvParser(ENV_PREFIX, meta, DEFAULT_PROFILE)
    meta_args_parser = ArgsParser(ARGS_PREFIX, PROFILE_KEY, DEFAULT_PROFILE, meta)
    layers = [meta, meta_env_parser(), meta_args_parser()]
    meta = freeze(reduce(merge_layers, layers, {}))

    if meta.file is None:
        sys.exit('file meta param is missing')

    paths = meta.file
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

    if meta.dot_env_file is not None:
        parser = DotEnvParser(self, meta.dot_env_file, target_profile=meta.profile)
        params = parser()
        if len(params) > 0:
            layers.append(params)

    if meta.env_prefix is not None:
        parser = EnvParser(meta.env_prefix, layers[0], meta.default_profile, target_profile=meta.profile)
        params = parser()
        if len(params) > 0:
            layers.append(params)

    if meta.args_prefix is not None:
        parser = ArgsParser(meta.args_prefix, meta.profile_key, meta.default_profile,
                            layers[0], target_profile=meta.profile)
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
    profile_params['__profile__'] = [default_profile]
    if profile != default_profile:
        active_profile_params = params[profile]
        merge_layers(profile_params, active_profile_params)
        profile_params['__profile__'].append(profile)
    return profile_params


def merge_layers(dst: dict, src: dict, path='') -> dict:
    for src_key, src_value in src.items():
        if src_key == '__source__':
            if not src_key in dst:
                dst[src_key] = []
            dst[src_key].extend(src_value)
        elif isinstance(src_value, dict) and isinstance(dst.get(src_key), dict):
            merge_layers(dst[src_key], src_value, f'{path}.{src_key}')
        elif isinstance(src_value, list) and isinstance(dst.get(src_key), list) and len(src_value) == len(dst[src_key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                current_path = f'{path}[{i}]'
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    merge_layers(dst_item[i], src_value[i], current_path)
                else:
                    dst_item[i] = convert_type(dst_item[i], src_value[i], current_path)
        else:
            dst[src_key] = convert_type(dst.get(src_key), src_value, f'{path}.{src_key}')
    return dst
