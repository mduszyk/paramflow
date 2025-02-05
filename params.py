from frozen_attr_dict import FrozenAttrDict
from parser import TomlParser, YamlParser, JsonParser, EnvParser, ArgsParser


parser_map = {
    'toml': TomlParser,
    'yaml': YamlParser,
    'json': JsonParser,
}

def load_params(paths, env_prefix=None, args_prefix=None, profile_key='params_profile', **kwargs):
    if not isinstance(paths, list):
        paths = [paths]
    full_parsers = []
    for path in paths:
        ext = path.split('.')[-1]
        parser_class = parser_map[ext]
        full_parsers.append(parser_class(path))
    parsers = []
    if env_prefix is not None:
        parsers.append(EnvParser(env_prefix))
    if args_prefix is not None:
        parsers.append(ArgsParser(args_prefix, profile_key))
    return merge_params(full_parsers, parsers, profile_key=profile_key, **kwargs)


def merge_params(full_parsers, parsers, profile=None, profile_key='params_profile'):
    full_params = {}
    for parser in full_parsers:
        update_leaves(parser(), full_params)

    profile_params = full_params.get('default', {})

    params = {}
    for parser in parsers:
        update_leaves(parser(profile_params), params)

    if profile is None:
        profile = params.get(profile_key)

    if profile is not None:
        update_leaves(full_params[profile], profile_params)

    update_leaves(params, profile_params)

    return FrozenAttrDict(profile_params)


def update_leaves(src, dst):
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            update_leaves(value, dst[key])
        else:
            dst[key] = value
