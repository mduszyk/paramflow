import argparse
import configparser
import json
import os
from typing import Dict, Final, Type
from abc import ABC, abstractmethod

import yaml


class Parser(ABC):
    @abstractmethod
    def __call__(self, *args) -> Dict[str, any]:
        pass


class TomlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self, *args) -> Dict[str, any]:
        import tomllib
        with open(self.path, 'rb') as fp:
            params = tomllib.load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class YamlParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self, *args) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            params = yaml.safe_load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class JsonParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self, *args) -> Dict[str, any]:
        with open(self.path, 'r') as fp:
            params = json.load(fp)
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class IniParser(Parser):

    def __init__(self, path: str):
        self.path = path

    def __call__(self, *args) -> Dict[str, any]:
        config = configparser.ConfigParser()
        config.read(self.path)
        params = {section: dict(config.items(section)) for section in config.sections()}
        if len(params) > 0:
            params['__source__'] = [self.path]
        return params


class DotEnvParser(Parser):

    def __init__(self, path: str, prefix: str, default_profile: str, target_profile: str = None):
        self.path = path
        self.prefix = prefix
        self.default_profile = default_profile
        self.target_profile = target_profile

    def __call__(self, params: Dict[str, any]) -> Dict[str, any]:
        from dotenv import dotenv_values
        if self.target_profile is None and self.default_profile in params:
            self.target_profile = self.default_profile
        params = params.get(self.default_profile, params)
        env = dotenv_values(self.path)
        params = get_env_params(env, self.prefix, params)
        if len(params) > 0:
            if self.target_profile is not None:
                params = {self.target_profile: params}
            if len(params) > 0:
                params['__source__'] = [self.path]
        return params


def get_env_params(env: Dict[str, any], prefix: str, ref_params: Dict[str, any]) -> Dict[str, any]:
    params = {}
    for env_key, env_value in env.items():
        if env_key.startswith(prefix):
            key = env_key.replace(prefix, '').lower()
            if key in ref_params:
                params[key] = env_value
    return params


class EnvParser(Parser):

    def __init__(self, prefix: str, default_profile: str, target_profile: str = None):
        self.prefix = prefix
        self.default_profile = default_profile
        self.target_profile = target_profile

    def __call__(self, params: Dict[str, any]) -> Dict[str, any]:
        if self.target_profile is None and self.default_profile in params:
            self.target_profile = self.default_profile
        params = params.get(self.default_profile, params)
        env_params = get_env_params(os.environ, self.prefix, params)
        result = env_params
        if len(env_params) > 0:
            if self.target_profile is not None:
                result = {self.target_profile: env_params}
            if len(env_params) > 0:
                result['__source__'] = ['env']
        return result


class ArgsParser(Parser):

    def __init__(self, prefix: str, default_profile: str, target_profile: str = None):
        self.prefix = prefix
        self.default_profile = default_profile
        self.target_profile = target_profile

    def __call__(self, params: Dict[str, any]) -> Dict[str, any]:
        if self.target_profile is None and self.default_profile in params:
            self.target_profile = self.default_profile
        params = params.get(self.default_profile, params)
        parser = argparse.ArgumentParser()
        for key, value in params.items():
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
        if len(args_params) > 0:
            if self.target_profile is not None:
                result = {self.target_profile: args_params}
            if len(args_params) > 0:
                result['__source__'] = ['args']
        return result


PARSER_MAP: Final[Dict[str, Type[Parser]]] = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
    'ini': IniParser,
}
