# paramflow
ParamFlow is a lightweight and versatile library for managing hyperparameters
and configurations, tailored for machine learning projects and applications
requiring layered parameter handling. It merges parameters from multiple
sources, generates command-line argument parsers, and simplifies parameter
overrides, providing a seamless and efficient experience.

## Features
- **Layered configuration**: Merge parameters from files, environment variables, and command-line arguments.
- **Immutable dictionary**: Provides a read-only dictionary with attribute-style access.
- **Profile support**: Manage multiple sets of parameters with profile-based layering.
- **Layered meta-parameters**: `paramflow` configures itself using a layered approach.
- **Automatic type conversion**: Converts types during merging based on target parameter types.
- **Command-line argument parsing**: Automatically generates an `argparse` parser from parameter definitions.
- **Nested Configuration**: Allows for nested configuration and merging.

## Installation
```sh
pip install paramflow
```
Install with `.env` support:
```sh
pip install "paramflow[dotenv]"
```

## Basic Usage
### Example Configuration File (`params.toml`)
```toml
[default]
learning_rate = 0.001
batch_size = 64
```

### Loading Parameters in Python (`app.py`)
```python
import paramflow as pf

params = pf.load('params.toml')
print(params.learning_rate)  # 0.001
```

### Generating Command-line Help
Running the script with `--help` displays both meta-parameters and parameters:
```sh
python app.py --help
```

## Meta-Parameter Layering
Meta-parameters control how `paramflow.load` reads its own configuration. Layering order:
1. `paramflow.load` arguments
2. Environment variables (default prefix: `P_`)
3. Command-line arguments (`argparse`)

### Activating Profiles
Via command-line:
```sh
python print_params.py --profile dqn-adam
```
Via environment variable:
```sh
P_PROFILE=dqn-adam python print_params.py
```

## Parameter Layering
Parameters are merged from multiple sources in the following order:
1. Configuration files (`.toml`, `.yaml`, `.ini`, `.json`, `.env`)
2. Environment variables (default prefix: `P_`)
3. Command-line arguments (`argparse`)

### Customizing Layering Order
You can specify the order explicitly (`env` and `args` are reserved names):
```python
params = pf.load('params.toml', 'env', '.env', 'args')
```

### Overriding Parameters
Override parameters via command-line arguments:
```sh
python print_params.py --profile dqn-adam --learning_rate 0.0002
```

## Managing ML Hyperparameter Profiles
### Example Configuration (`params.toml`)
```toml
[default]
learning_rate = 0.00025
batch_size = 32
optimizer_class = 'torch.optim.RMSprop'
optimizer_kwargs = { momentum = 0.95 }
random_seed = 13

[adam]
learning_rate = 1e-4
optimizer_class = 'torch.optim.Adam'
optimizer_kwargs = {}
```

### Activating a Profile
```sh
python app.py --profile adam
```
This overrides:
- `learning_rate` → `1e-4`
- `optimizer_class` → `torch.optim.Adam`
- `optimizer_kwargs` → `{}`

## Managing Development Stages
Profiles can be used to manage configurations for different environments.

### Example Configuration (`params.toml`)
```toml
[default]
debug = true
database_url = "mysql://localhost:3306/myapp"

[dev]
database_url = "mysql://dev:3306/myapp"

[prod]
debug = false
database_url = "mysql://prod:3306/myapp"
```

### Activating a Profile
```sh
export P_PROFILE=dev
python app.py
```

