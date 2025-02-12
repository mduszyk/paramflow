# paramflow
A parameter and configuration management library motivated by training machine learning models
and managing configuration for applications that require profiles and layered parameters.
```paramflow``` is designed for flexibility and ease of use, enabling seamless parameter merging
from multiple sources. It also auto-generates a command-line argument parser and allows for
easy parameter overrides.

## Features
- **Layered configuration**: Merge parameters from files, environment variables, and command-line arguments.
- **Immutable dictionary**: Provides a read-only dictionary with attribute-style access.
- **Profile support**: Manage multiple sets of parameters. Layer the chosen profile on top of the default profile.
- **Layered meta-parameters**: ```paramflow``` loads its own configuration using layered approach.
- **Convert types**: Convert types during merging using target parameters as a reference for type conversions.
- **Generate argument parser**: Use parameters defined in files as a reference for generating ```argparse``` parser.

## Usage
Install:
```shell
pip install paramflow
```
Install with ```.env``` support:
```shell
pip install paramflow[dotenv]
```

```params.toml```
```toml
[default]
learning_rate = 0.001
```

```app.py```
```python
import paramflow as pf
params = pf.load(source='params.toml')
print(params.learning_rate)
```

## Meta-parameter Layering
Meta-parameter layering controls how ```paramflow.load``` reads its own configuration.

Layering order:
1. ```paramflow.load``` arguments.
2. Environment variables (default prefix ```P_```).
3. Command-line arguments (via ```argparse```).

Activate profile using command-line arguments:
```shell
python print_params.py --profile dqn-adam
```
Activate profile using environment variable:
```shell
P_PROFILE=dqn-adam python print_params.py
```

## Parameter Layering
Parameter layering merges parameters from multiple sources.

Layering order:
1. Configuration files (```.toml```, ```.yaml```, ```.ini```, ```.json```).
2. ```.env``` file.
3. Environment variables (default prefix ```P_```).
4. Command-line arguments (via ```argparse```).

Layering order can be customized via ```source``` argument to ```param.flow```.
```python
params = pf.load(source=['params.toml', 'env', '.env', 'args'])
```
 
Overwrite parameter value:
```shell
python print_params.py --profile dqn-adam --lr 0.0002
```

## ML hyper-parameters profiles
```params.toml```
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
Activating adam profile
```shell
python app.py --profile adam
```
will result in overwriting default learning rate with ```1e-4```, default optimizer class with ```torch.optim.Adam```
and default optimizer arguments with and empty dict.

## Development stages profiles
Profiles can be used to manage software development stages.
```params.toml```:
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
Activate prod profile:
```shell
export P_PROFILE=dev
python app.py
```
