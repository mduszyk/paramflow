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


class EnvParser(Parser):

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self) -> Dict[str, any]:
        env_params = {}
        for env_key, env_value in os.environ.items():
            if env_key.startswith(self.prefix):
                key = env_key.replace(self.prefix, '').lower()
                env_params[key] = env_value
        return env_params


class ArgsParser(Parser):

    def __init__(self, prefix: str, profile_key: str, default_profile: str, params: Dict[str, any]):
        self.prefix = prefix
        self.profile_key = profile_key
        self.params = params.get(default_profile, params)

    def __call__(self) -> Dict[str, any]:
        parser = argparse.ArgumentParser()
        parser.add_argument(f'--{self.prefix}{self.profile_key}', type=str, default=None,
                            help='name of the profile to activate')
        for key, value in self.params.items():
            typ = type(value)
            if typ is dict or typ is list or typ is bool:
                typ = str
            parser.add_argument(f'--{self.prefix}{key}', type=typ, default=None, help=f'{key} = {value}')
        args, _ = parser.parse_known_args()
        args_params = {}
        for arg_key, arg_value in args.__dict__.items():
            if arg_value is not None:
                key = arg_key.replace(self.prefix, '')
                args_params[key] = arg_value
        return args_params
