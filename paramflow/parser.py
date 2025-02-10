import argparse
import configparser
import json
import os
import tomllib
from typing import Dict, Final, Type
from abc import ABC, abstractmethod

import yaml
from dotenv import dotenv_values


class Parser(ABC):
    @abstractmethod
    def __call__(self) -> Dict[str, any]:
        pass


class TomlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'rb') as fp:
            params = tomllib.load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class YamlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            params = yaml.safe_load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class JsonParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            params = json.load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class IniParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self):
        config = configparser.ConfigParser()
        config.read(self.path)
        params = {section: dict(config.items(section)) for section in config.sections()}
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class DotEnvParser(Parser):

    def __init__(self, path: str, target_profile: str = None):
        self.path = path
        self.target_profile = target_profile

    def __call__(self):
        params = dotenv_values(self.path)
        if self.target_profile is not None:
            result = {self.target_profile: env_params}
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class EnvParser(Parser):

    def __init__(self, prefix: str, params: Dict[str, any], default_profile, target_profile=None):
        self.prefix = prefix
        self.params = params
        self.params = params.get(default_profile, params)
        self.target_profile = target_profile

    def __call__(self) -> Dict[str, any]:
        env_params = {}
        for env_key, env_value in os.environ.items():
            if env_key.startswith(self.prefix):
                key = env_key.replace(self.prefix, '').lower()
                if key in self.params:
                    env_params[key] = env_value
        result = env_params
        if self.target_profile is not None:
            result = {self.target_profile: env_params}
        if len(env_params) > 0:
            result['__source__'] = ['environment']
        return result


class ArgsParser(Parser):

    def __init__(self, prefix: str, profile_key: str, default_profile: str,
                 params: Dict[str, any], target_profile=None):
        self.prefix = prefix
        self.profile_key = profile_key
        self.params = params.get(default_profile, params)
        self.target_profile = target_profile

    def __call__(self) -> Dict[str, any]:
        parser = argparse.ArgumentParser()
        for key, value in self.params.items():
            typ = type(value)
            if typ is dict or typ is list or typ is bool or value is None:
                typ = str
            parser.add_argument(f'--{self.prefix}{key}', type=typ, default=None, help=f'{key} = {value}')
        args, _ = parser.parse_known_args()
        args_params = {}
        for arg_key, arg_value in args.__dict__.items():
            if arg_value is not None:
                key = arg_key.replace(self.prefix, '')
                args_params[key] = arg_value
        result = args_params
        if self.target_profile is not None:
            result = {self.target_profile: args_params}
        if len(args_params) > 0:
            result['__source__'] = ['arguments']
        return result


PARSER_MAP: Final[Dict[str, Type[Parser]]] = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
    'ini': IniParser,
}
