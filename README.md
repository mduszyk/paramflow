# paramflow
[![tests](https://github.com/mduszyk/paramflow/actions/workflows/test.yml/badge.svg)](https://github.com/mduszyk/paramflow/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/paramflow)](https://pypi.org/project/paramflow/)

ParamFlow is a lightweight library for layered configuration management, tailored for machine learning projects and any application that needs to merge parameters from multiple sources. It merges files, environment variables, and CLI arguments in a defined order, activates named profiles, and returns a read-only, attribute-accessible dictionary.

**Requires Python 3.11+**

## Design philosophy

ParamFlow is intentionally minimalist. You define parameters once in a config file — no schemas, no type annotations, no boilerplate. Types are inferred from the values in the config file and automatically applied when overriding via environment variables or CLI arguments. The goal is to keep configuration code as small as possible: one `pf.load()` call is all you need.

## Features
- **Layered configuration**: Merge parameters from files, environment variables, and CLI arguments in a defined order.
- **Profile support**: Manage multiple named parameter sets; activate one at runtime.
- **Immutable result**: Parameters are returned as a frozen, attribute-accessible dictionary.
- **Schema-free type inference**: Types come from the config file values — no annotations required.
- **Auto-generated CLI parser**: Every parameter becomes a `--flag` automatically, with types and defaults inferred from the config.
- **Layered meta-parameters**: `paramflow` configures itself (sources, profile, prefixes) using the same layered approach.
- **Nested configuration**: Deep-merges nested dicts across layers; individual subkeys overridable via `key__subkey` syntax in env vars and CLI args.

## Installation
```sh
pip install paramflow
```
With `.env` file support:
```sh
pip install "paramflow[dotenv]"
```

## Supported formats

| Format | Extension | Notes |
|--------|-----------|-------|
| TOML   | `.toml`   | Recommended; native types |
| YAML   | `.yaml`   | Requires `pyyaml` |
| JSON   | `.json`   | |
| INI    | `.ini`    | All values are strings; type conversion only works when a typed value already exists in a preceding layer |
| dotenv | `.env`    | Requires `paramflow[dotenv]`; filtered by prefix |

## Basic usage

**`params.toml`**
```toml
[default]
learning_rate = 0.001
batch_size = 64
debug = true
```

**`app.py`**
```python
import paramflow as pf

params = pf.load('params.toml')
print(params.learning_rate)  # 0.001
print(params.batch_size)     # 64
```

Run with `--help` to see all parameters and meta-parameters:
```sh
python app.py --help
```

## Parameter layering

Parameters are merged in the order sources are listed. Later sources override earlier ones. By default, `env` and `args` are appended automatically:

```
params.toml  →  env vars  →  CLI args
```

You can pass multiple files — each layer overrides keys from the previous:
```python
params = pf.load('base.toml', 'overrides.toml')
```

To control the order explicitly, pass all sources as positional arguments (`'env'` and `'args'` are reserved names for environment variables and CLI arguments respectively):
```python
params = pf.load('params.toml', 'env', 'overrides.env', 'args')
```

To disable auto-appending of env or args sources, pass `None` as env and args prefixes:
```python
params = pf.load('params.toml', env_prefix=None, args_prefix=None)
```

### Inline dicts as sources

Plain dicts can be mixed into the source list:
```python
params = pf.load('params.toml', {'debug': False, 'extra_key': 'value'})
```
This can be used to for example set default values or use params loaded into dict in completely custom way.

### Type inference

No type declarations are needed anywhere. The type of each value in the config file is used as the target type when merging from env vars or CLI args. For example, if `batch_size = 32` is in the config, then `--batch_size 64` from the CLI is automatically converted to `int`. Booleans, floats, dicts, and lists all work the same way.

### Nested parameters

Nested parameters can be overridden using `__` (double underscore) as the separator, both in env vars and CLI args:

**`params.toml`**
```toml
[default.optimizer]
lr = 0.001
momentum = 0.9
```

Override a single subkey via CLI:
```sh
python app.py --optimizer__lr 0.0001
```

Or via environment variable:
```sh
P_OPTIMIZER__LR=0.0001 python app.py
```

Any depth is supported:
```sh
python app.py --a__b__c 42
```

### Key filtering for env vars and CLI args

Env vars and CLI args only override keys that **already exist** in the preceding layers. A `P_NEW_KEY` with no matching key in the config file is silently ignored. This keeps the config file the authoritative schema.

## Profiles

Profiles let you define named parameter sets that layer on top of `[default]`.

**`params.toml`**
```toml
[default]
learning_rate = 0.001
batch_size = 32
debug = true

[prod]
debug = false
batch_size = 128
```

Activate a profile via CLI:
```sh
python app.py --profile prod
```

Or via environment variable:
```sh
P_PROFILE=prod python app.py
```

Or directly in code:
```python
params = pf.load('params.toml', profile='prod')
```

## Overriding parameters at runtime

Any parameter can be overridden on the command line:
```sh
python app.py --profile prod --learning_rate 0.0001 --batch_size 64
```

Or via environment variable (default prefix `P_`, uppercased):
```sh
P_LEARNING_RATE=0.0001 python app.py
```

## Meta-parameter layering

Meta-parameters control how `pf.load` reads its own configuration (which sources to load, which profile to activate, what prefixes to use). They follow the same layering order:

1. `pf.load(...)` keyword arguments
2. Environment variables (default prefix: `P_`)
3. CLI arguments

This means you can pass a config file path entirely from the command line without hardcoding it:
```sh
python app.py --sources params.toml
```

Or point to a different config via env:
```sh
P_SOURCES=prod_params.toml python app.py
```

## Metadata keys

Every result includes two metadata keys:

- `__source__`: list of all sources that contributed parameters, in merge order
- `__profile__`: list of activated profiles, e.g. `['default', 'prod']`

```python
params = pf.load('params.toml')
print(params.__source__)   # ['params.toml', 'env', 'args']
print(params.__profile__)  # ['default']
```

## Freezing and unfreezing

`pf.load` returns a `ParamsDict` — an immutable, attribute-accessible dict. You can freeze/unfreeze manually when needed (e.g. for serialization):

```python
plain = pf.unfreeze(params)   # convert to plain dict/list tree
frozen = pf.freeze(plain)     # convert back to ParamsDict/ParamsList
```

Accessing a missing key raises `AttributeError` with the parameter name:
```python
params.nonexistent  # AttributeError: 'ParamsDict' has no param 'nonexistent'
```

## Example: ML hyperparameter profiles

**`params.toml`**
```toml
[default]
learning_rate = 0.00025
batch_size = 32
optimizer = 'torch.optim.RMSprop'
random_seed = 13

[adam]
learning_rate = 1e-4
optimizer = 'torch.optim.Adam'
```

```sh
python train.py --profile adam --learning_rate 0.0002
```

## Example: environment-based deployment config

**`params.yaml`**
```yaml
default:
  debug: true
  database_url: "mysql://localhost:3306/myapp"

dev:
  database_url: "mysql://dev:3306/myapp"

prod:
  debug: false
  database_url: "mysql://prod:3306/myapp"
```

```sh
export P_PROFILE=prod
python app.py
```
