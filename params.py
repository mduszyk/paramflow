import argparse
import json
import os
import tomllib


class FrozenAttrDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, '__dict__', self)

    def __setattr__(self, key, value):
        raise AttributeError('FrozenAttrDict is immutable')

    def __delattr__(self, key):
        raise AttributeError('FrozenAttrDict is immutable')

    def __setitem__(self, key, value):
        raise TypeError('FrozenAttrDict is immutable')

    def __delitem__(self, key):
        raise TypeError('FrozenAttrDict is immutable')


def load_params(path, profile=None, env_prefix=None, args_prefix=None):
    with open(path, 'rb') as f:
        all_params = tomllib.load(f)
        params = all_params.get('default', {})

    args = None
    if args_prefix is not None:
        args = parse_args(params, args_prefix)

    if profile is None:
        if env_prefix is not None:
            profile = os.environ.get(env_prefix + 'PARAMS_PROFILE')
        if args_prefix is not None:
            profile = args.__dict__.get(args_prefix + 'params_profile')

    if profile is not None:
        params.update(all_params[profile])

    if env_prefix is not None:
        update_from_env(params, env_prefix)

    if args_prefix is not None:
        update_from_args(params, args, args_prefix)

    return FrozenAttrDict(params)


def update_from_env(params, env_prefix):
    for env_key, env_value in os.environ.items():
        if env_key.startswith(env_prefix):
            key = env_key.replace(env_prefix, '').lower()
            value = params.get(key)
            if value is not None and not isinstance(value, str):
                if isinstance(value, dict) or isinstance(value, list):
                    env_value = json.loads(env_value)
                elif isinstance(value, bool):
                    env_value = env_value.lower() == 'true'
                else:
                    env_value = type(value)(env_value)
            params[key] = env_value


def parse_args(params, args_prefix):
    parser = argparse.ArgumentParser()
    parser.add_argument(f'--{args_prefix}params_profile', type=str, default=None)
    for key, value in params.items():
        parser.add_argument(f'--{args_prefix}{key}', type=type(value), default=None)
    return parser.parse_args()


def update_from_args(params, args, args_prefix):
    for arg_key, arg_value in args.__dict__.items():
        if arg_value is not None:
            key = arg_key.replace(args_prefix, '')
            params[key] = arg_value
