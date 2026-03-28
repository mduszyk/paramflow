# paramflow
[![tests](https://github.com/mduszyk/paramflow/actions/workflows/test.yml/badge.svg)](https://github.com/mduszyk/paramflow/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/paramflow)](https://pypi.org/project/paramflow/)

- one `pf.load()` call
- result is a plain Python dict
- env vars and CLI args handled automatically

ParamFlow is a lightweight library for layered configuration management, tailored for machine learning projects and any application that needs to merge parameters from multiple sources. It merges files, environment variables, and CLI arguments in a defined order, activates named profiles, and returns a read-only, attribute-accessible dict that is fully compatible with the Python `dict` API.

**Requires Python 3.11+**

## Design philosophy

ParamFlow is intentionally minimalist. You define parameters once in a config file — no schemas, no type annotations, no boilerplate. Types are inferred from the values in the config file and automatically applied when overriding via environment variables or CLI arguments. One `pf.load()` call is all you need, and the result is a plain Python dict — works anywhere a dict does: `json.dumps`, `**unpacking`, serialization libraries, all without conversion.

## Features
- **Layered configuration**: Merge parameters from files, environment variables, and CLI arguments in a defined order. Config file is optional — pure env/args loading is supported.
- **`.env` support**: `.env` files can be listed explicitly as a source alongside other config files.
- **Profile support**: Manage multiple named parameter sets; activate one at runtime.
- **Immutable result**: Parameters are returned as a frozen, attribute-accessible dict fully compatible with the Python `dict` API.
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
| INI    | `.ini`    | Values are type-inferred (`int`, `float`, `bool`, `str`) |
| dotenv | `.env`    | Requires `paramflow[dotenv]`; values type-inferred |

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

Because the result is a plain Python dict, it works anywhere a dict does — no conversion needed:
```python
import json

print(json.dumps(params))  # serialize for logging, no conversion needed
```

## Parameter layering

Parameters are merged in the order sources are listed. Later sources override earlier ones. By default, `env` and `args` are appended automatically — they are the only implicit sources; everything else must be listed explicitly:

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

### File-free loading

No config file is required. You can load purely from environment variables or CLI arguments — useful for containerized workloads where config comes entirely from the environment:

```python
params = pf.load()  # env vars and CLI args only
```

```sh
P_LR=0.001 P_BATCH_SIZE=32 python app.py
# or
python app.py --lr 0.001 --batch_size 32
```

Without a config file, there is no reference type to guide conversion, so all values are type-inferred (`int`, `float`, `bool`, or `str`).

### `.env` files

`.env` files are listed explicitly as sources, keeping configuration loading transparent:

```python
params = pf.load('params.toml', '.env')
```

This merges the TOML file first, then applies any prefixed vars from `.env` on top. As with all sources, later entries override earlier ones.

### Inline dicts as sources

Plain dicts can be mixed into the source list:
```python
params = pf.load('params.toml', {'debug': False, 'extra_key': 'value'})
```
This can be used to set default values, or to inject params loaded via a completely custom method. Note: a plain dict without a `'default'` key is treated as profile-less and merged directly — wrap it in `{'default': {...}}` if you want it to participate in profile layering.

### Type inference

No type declarations are needed anywhere. Types are handled automatically in all cases:

- **Config file present** (TOML, YAML, JSON): the type of each value in the config is used as the target type when overriding via env vars or CLI args. `batch_size = 32` in the config means `--batch_size 64` and `P_BATCH_SIZE=64` both produce `int(64)`.
- **No config file** (pure env/args): values are inferred in order — `int`, `float`, `bool`, then `str`. `P_LR=0.001` produces `float(0.001)`, `P_DEBUG=true` produces `bool(True)`.
- **INI files**: since INI has no native types, `infer_type` is applied to every value on load, same as the no-schema case.

The result is consistent behavior regardless of source format — you always get the most specific type possible without declaring anything.

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

### Env vars and CLI args key behaviour

Any env var with the prefix and any CLI arg is accepted — including keys not present in the config file. If the key exists in the config, the reference type is used for conversion. If it doesn't exist, `infer_type` is applied and the key is added to the result — same behaviour as file-free mode.

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

## `pf.load()` reference

```python
pf.load(*sources, env_prefix, args_prefix, meta_env_prefix, meta_args_prefix, profile_key, default_profile, profile)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `*sources` | `()` | File paths (`.toml`, `.yaml`, `.json`, `.ini`, `.env`) or dicts to merge in order. `'env'` and `'args'` are reserved source names. |
| `env_prefix` | `'P_'` | Prefix for environment variables. Set to `None` to disable env source. |
| `args_prefix` | `''` | Prefix for CLI arguments. Set to `None` to disable args source. |
| `meta_env_prefix` | `'P_'` | Prefix for env vars that override meta-parameters. |
| `meta_args_prefix` | `''` | Prefix for CLI args that override meta-parameters. |
| `profile_key` | `'profile'` | Name of the meta-parameter used to select a profile. |
| `default_profile` | `'default'` | Name of the base profile section in config files. |
| `profile` | `None` | Profile to activate on top of `default_profile`. |

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

`pf.load` returns a `ParamsDict` — an immutable, attribute-accessible dict. You can freeze/unfreeze manually when needed (e.g. when you need a mutable copy):

```python
plain = pf.unfreeze(params)   # convert to plain dict/list tree
frozen = pf.freeze(plain)     # convert back to ParamsDict/ParamsList
```

Lists in the result are wrapped in `ParamsList`, an immutable list subclass.

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

## Example: research experiments

Profiles map naturally to experiment variants. Define a baseline and override only what changes per experiment — no duplicated config, no separate files per run.

**`params.toml`**
```toml
[default]
model = 'resnet18'
learning_rate = 0.001
batch_size = 64
dropout = 0.3
epochs = 50
random_seed = 42

[large]
model = 'resnet50'
batch_size = 32

[no_dropout]
dropout = 0.0

[high_lr]
learning_rate = 0.01
epochs = 30
```

**`train.py`**
```python
import json
import paramflow as pf

params = pf.load('params.toml')

# log exact config for reproducibility — one line, works because result is a plain dict
print(json.dumps(params))

# run experiment...
```

Run a specific variant:
```sh
python train.py --profile large
```

Override a single value on top of a profile:
```sh
python train.py --profile large --learning_rate 0.0005
```

Run with env vars:
```sh
P_PROFILE=no_dropout P_RANDOM_SEED=123 python train.py
```

The logged config always includes `__source__` and `__profile__`, so you know exactly what ran:
```json
{"model": "resnet18", "learning_rate": 0.001, "batch_size": 64, "dropout": 0.0,
 "epochs": 50, "random_seed": 42, "__source__": ["params.toml", "env", "args"],
 "__profile__": ["default", "no_dropout"]}
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

**`app.py`**
```python
import paramflow as pf

params = pf.load('params.yaml')
print(params.debug)         # False
print(params.database_url)  # mysql://prod:3306/myapp
```

```sh
export P_PROFILE=prod
python app.py
```

## Example: containerized / twelve-factor app

Parameters come entirely from environment variables — the [twelve-factor](https://12factor.net/config) way. A `.env` file is listed as a source for local development; in production, env vars are injected by the container runtime and override .env entries.

**`app.py`**
```python
import paramflow as pf

params = pf.load('.env')  # reads from .env first, then env vars override it in production deployment

print(params.db_url)   # postgres://localhost/mydb
print(params.debug)    # True
print(params.port)     # 8080
```

**`.env`** (local development, not committed to version control)
```
P_DB_URL=postgres://localhost/mydb
P_DEBUG=true
P_PORT=8080
```

Run locally
```sh
python app.py
```

Run in production — env vars injected by the container override entries in `.env`:
```sh
docker run \
  -e P_DB_URL=postgres://prod-db/mydb \
  -e P_DEBUG=false \
  -e P_PORT=8080 \
  myapp
```
