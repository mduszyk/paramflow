import logging
import sys
from typing import List, Dict, Optional, Final, Tuple

from paramflow.convert import convert_type
from paramflow.frozen import freeze, ParamsDict
from paramflow.parser import PARSER_MAP, EnvParser, ArgsParser, DotEnvParser, Parser, DictParser

logger = logging.getLogger(__name__)

ENV_SOURCE: Final[str] = 'env'
ARGS_SOURCE: Final[str] = 'args'


def load(*sources: str | Tuple[str, ...] | dict | Tuple[dict, ...],
         meta_env_prefix: str = 'P_',
         meta_args_prefix: str = '',
         env_prefix: str = 'P_',
         args_prefix: str = '',
         profile_key: str = 'profile',
         default_profile: str = 'default',
         profile: Optional[str] = None) -> ParamsDict[str, any]:
    """
    Load parameters form multiple sources, layer them on top of each other and activate profile.
    Activation of profile means learying it on top of the default profile.
    :param sources: file or multiple files to load parameters from
    :param meta_env_prefix: prefix for env vars that are used to overwrite meta params
    :param meta_args_prefix: prefix for command-line arguments to overwrite meta params
    :param env_prefix: prefix for env vars that are used to overwrite params, if None disable auto adding env source
    :param args_prefix: prefix for command-line arguments, if None disable auto adding args source
    :param profile_key: parameter name for the profile
    :param default_profile: default profile
    :param profile: profile to activate
    :return: read-only parameters as frozen dict
    """

    logger.debug('Reading meta params layer %d, source: %s', 0, 'pf.load')
    meta = {
        'sources': sources,
        'env_prefix': env_prefix,
        'args_prefix': args_prefix,
        'profile_key': profile_key,
        'default_profile': default_profile,
        profile_key: profile,
        '__source__': ['pf.load'],
    }
    logger.debug('Reading meta params layer %d, source: %s', 1, 'env')
    meta_env_parser = EnvParser(meta_env_prefix, 'default')
    logger.debug('Reading meta params layer %d, source: %s', 2, 'args')
    meta_args_parser = ArgsParser(meta_args_prefix, 'default',
                                  no_exit=True, consume_args=True, descr='Meta-parameters')
    meta = deep_merge(meta, meta_env_parser(meta))
    meta = deep_merge(meta, meta_args_parser(meta))
    meta = freeze(meta)

    if meta.sources is None or len(meta.sources) == 0:
        sys.exit('sources meta param is missing')

    sources = list(meta.sources)

    if ENV_SOURCE not in sources and meta.env_prefix is not None:
        sources.append(ENV_SOURCE)
    if ARGS_SOURCE not in sources and meta.args_prefix is not None:
        sources.append(ARGS_SOURCE)
    parsers = build_parsers(sources, meta)

    return parse(parsers, meta.default_profile, meta.profile)


def parse(parsers: List[Parser], default_profile: str, target_profile: str):
    params = {}
    for parser in parsers:
        params = deep_merge(params, parser(params))
    params = activate_profile(params, default_profile, target_profile)
    return freeze(params)


def build_parsers(sources: List[str], meta: Dict[str, any]):
    parsers = []
    for i, source in enumerate(sources):
        logger.info('Reading params layer %d, source: %s', i, source)
        if isinstance(source, dict):
            parser = DictParser(source)
        elif source == ARGS_SOURCE:
            parser = ArgsParser(meta.args_prefix, meta.default_profile, meta.profile, descr='Parameters')
        elif source == ENV_SOURCE:
            parser = EnvParser(meta.env_prefix, meta.default_profile, meta.profile)
        elif source.endswith('.env'):
            parser = DotEnvParser(source, meta.env_prefix, meta.default_profile, meta.profile)
        else:
            ext = source.split('.')[-1]
            parser_class = PARSER_MAP[ext]
            parser = parser_class(source)
        parsers.append(parser)
    return parsers


def activate_profile(params: Dict[str, any], default_profile: str, profile: str) -> Dict[str, any]:
    profile_params = params.get(default_profile)
    if profile_params is None:
        profile_params = params  # profiles disabled
    if '__source__' in params:
        profile_params['__source__'] = params['__source__']
    profile_params['__profile__'] = [default_profile]
    if profile is not None and profile != default_profile:
        active_profile_params = params[profile]
        deep_merge(profile_params, active_profile_params)
        profile_params['__profile__'].append(profile)
    return profile_params


def deep_merge(dst: dict, src: dict, path: str = '') -> dict:
    for src_key, src_value in src.items():
        if src_key == '__source__':
            if not src_key in dst:
                dst[src_key] = []
            dst[src_key].extend(src_value)
        elif isinstance(src_value, dict) and isinstance(dst.get(src_key), dict) and len(src_value) > 0:
            deep_merge(dst[src_key], src_value, f'{path}.{src_key}')
        elif isinstance(src_value, list) and isinstance(dst.get(src_key), list) and len(src_value) == len(dst[src_key]):
            for i in range(len(src_value)):
                dst_item = dst[i]
                current_path = f'{path}[{i}]'
                if isinstance(src_value[i], dict) and isinstance(dst_item[i], dict):
                    deep_merge(dst_item[i], src_value[i], current_path)
                else:
                    dst_item[i] = convert_type(dst_item[i], src_value[i], current_path)
        else:
            dst[src_key] = convert_type(dst.get(src_key), src_value, f'{path}.{src_key}')
    return dst
