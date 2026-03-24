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
- **`.env` auto-discovery**: A `.env` file in the current directory is picked up automatically when no sources are specified.
- **Profile support**: Manage multiple named parameter sets; activate one at runtime.
- **Immutable result**: Parameters are returned as a frozen, attribute-accessible dict fully compatible with the Python `dict` API — works with `json.dumps`, `**unpacking`, and any serialization library without conversion.
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

Without a config file as a schema, all prefixed env vars and all CLI args are accepted. Values are type-inferred (`int`, `float`, `bool`, or `str`) in both cases.

### `.env` auto-discovery

If `pf.load()` is called with no sources and a `.env` file exists in the current directory, it is loaded automatically — no path needed:

```python
params = pf.load()  # picks up .env if present
```

This only triggers when no sources are explicitly provided. Explicit sources always take precedence.

### Inline dicts as sources

Plain dicts can be mixed into the source list:
```python
params = pf.load('params.toml', {'debug': False, 'extra_key': 'value'})
```
This can be used to for example set default values or use params loaded into dict in completely custom way.

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

Run on a SLURM cluster via env vars:
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

```sh
export P_PROFILE=prod
python app.py
```

## Example: containerized / twelve-factor app

No config file needed. Parameters come entirely from environment variables — the [twelve-factor](https://12factor.net/config) way. A `.env` file is picked up automatically in local development; in production, env vars are injected by the container runtime.

**`app.py`**
```python
import paramflow as pf

params = pf.load()  # no file — reads from .env locally, env vars in production

# read params
params.db_url
params.debug
params.port
```

**`.env`** (local development, not committed to version control)
```
P_DB_URL=postgres://localhost/mydb
P_DEBUG=true
P_PORT=8080
```

Run locally — `.env` is discovered automatically:
```sh
python app.py
```

Run in production — env vars injected by the container:
```sh
docker run \
  -e P_DB_URL=postgres://prod-db/mydb \
  -e P_DEBUG=false \
  -e P_PORT=8080 \
  myapp
```
