import json
from functools import reduce
from typing import List

from dparams.frozen import freeze
from dparams.parser import TomlParser, YamlParser, JsonParser, EnvParser, ArgsParser


parser_map = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
}

def load(paths,
         env_prefix='P_',
         args_prefix='',
         profile_key='params_profile',
         default_profile='default',
         active_profile=None):

    if not isinstance(paths, list):
        paths = [paths]

    profiles_params_layers = []
    for path in paths:
        ext = path.split('.')[-1]
        parser_class = parser_map[ext]
        parser = parser_class(path)
        params = parser()
        params['__source__'] = path
        profiles_params_layers.append(params)

    override_params_layers = []
    if env_prefix is not None:
        parser = EnvParser(env_prefix)
        env_params = parser(profiles_params_layers[0])
        env_params['__source__'] = 'environment'
        override_params_layers.append(env_params)
    if args_prefix is not None:
        parser = ArgsParser(args_prefix, profile_key)
        args_params = parser(profiles_params_layers[0])
        args_params['__source__'] = 'arguments'
        override_params_layers.append(args_params)

    return merge(profiles_params_layers, override_params_layers, profile_key, default_profile, active_profile)


def merge(profiles_params_layers: List[dict], override_params_layers: List[dict],
          profile_key: str, default_profile: str, active_profile: str):

    all_profiles_params = reduce(recursive_update, profiles_params_layers, {})
    override_params = reduce(recursive_update, override_params_layers, {})

    profile_params = all_profiles_params.get(default_profile)
    if profile_params is None:
        # profiles disabled
        profile_params = all_profiles_params

    if active_profile is None:
        params_active_profile = override_params.get(profile_key)
        if params_active_profile is not None:
            active_profile = params_active_profile
    if active_profile is not None:
        active_profile_params = all_profiles_params.get(active_profile)
        recursive_update(profile_params, active_profile_params)

    recursive_update(profile_params, override_params)

    return freeze(profile_params)


def recursive_update(dst: dict, src: dict):
    for key, src_value in src.items():
        if isinstance(src_value, dict) and isinstance(dst.get(key), dict):
            recursive_update(dst[key], src_value)
        elif isinstance(src_value, list) and isinstance(dst.get(key), list) and len(src_value) == len(dst[key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    recursive_update(dst_item[i], src_value[i])
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


def convert_type(dst_value, src_value):
    dst_type = type(dst_value)
    src_type = type(src_value)
    if dst_type is src_type:
        return src_value
    if dst_type is dict or dst_type is list:
        if src_type is str:
            return json.loads(src_value)
        raise TypeError(f'cannot override {src_type} by {dst_type}')
    elif dst_type is bool:
        return src_value.lower() == 'true'
    elif dst_value is None:
        return src_value
    else:
        return dst_type(src_value)
