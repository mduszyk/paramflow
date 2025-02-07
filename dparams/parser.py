import argparse
import json
import os
import tomllib
from typing import Dict

import yaml

from abc import ABC, abstractmethod


class Parser(ABC):
    @abstractmethod
    def __call__(self) -> Dict[str, any]:
        pass


class TomlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'rb') as fp:
            return tomllib.load(fp)


class YamlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            return yaml.safe_load(fp)


class JsonParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            return json.load(fp)


class UntypedParser(ABC):
    """ Parser for the source that doesn't support types. """
    @abstractmethod
    def __call__(self, params: Dict[str, any]) -> Dict[str, any]:
        pass


class EnvParser(UntypedParser):

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, params) -> Dict[str, any]:
        env_params = {}
        for env_key, env_value in os.environ.items():
            if env_key.startswith(self.prefix):
                key = env_key.replace(self.prefix, '').lower()
                type_ref = params.get(key)
                if type_ref is not None and not isinstance(type_ref, str):
                    if isinstance(type_ref, dict) or isinstance(type_ref, list):
                        env_value = json.loads(env_value)
                    elif isinstance(type_ref, bool):
                        env_value = env_value.lower() == 'true'
                    else:
                        env_value = type(type_ref)(env_value)
                env_params[key] = env_value
        return env_params


class ArgsParser(UntypedParser):

    def __init__(self, prefix: str, profile_key: str):
        self.prefix = prefix
        self.profile_key = profile_key

    def __call__(self, params) -> Dict[str, any]:
        parser = argparse.ArgumentParser()
        parser.add_argument(f'--{self.prefix}{self.profile_key}', type=str, default=None, help='profile name')
        for key, value in params.items():
            typ = type(value)
            if typ is dict or typ is list or typ is bool:
                typ = str
            parser.add_argument(f'--{self.prefix}{key}', type=typ, default=None, help=f'{key} = {value}')
        args = parser.parse_args()
        args_params = {}
        for arg_key, arg_value in args.__dict__.items():
            if arg_value is not None:
                key = arg_key.replace(self.prefix, '')
                args_params[key] = arg_value
        return args_params
