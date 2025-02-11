# paramflow
A parameter and configuration management library motivated by training machine learning models
and managing configuration for applications that require profiles and layered parameters.
```paramflow``` is designed for flexibility and ease of use, enabling seamless parameter merging
from multiple sources. It also auto-generates a command-line argument parser based on the first
parameter file and allows for easy parameter overrides.

## Features
- **Layered configuration**: Merge parameters from files, environment variables, and command-line arguments.
- **Immutable dictionary**: Provides a read-only dictionary with attribute-style access.
- **Profile support**: Manage multiple sets of parameters. Layer the chosen profile on top of the default profile.
- **Layered metaparameters**: ```paramflow``` loads its own configuration using layered approach.
- **Convert types**: Use first parameters file as a reference for type conversions.
- **Generate arg parser**: Use first parameters file as a reference for generating ```argparse``` parser.

## Usage
```python
import paramflow as pf
params = pf.load(file='dqn_params.toml')
print(params.lr)
```

## Metaparameter Layering (Controls paramflow.load)
1. ```paramflow.load(...)``` arguments
2. Environment variables (default prefix 'P_')
3. Command-line arguments (via ```argparse```)

### Example
Activate profile using command-line arguments:
```bash
python print_params.py --profile dqn-adam
```
Activate profile using environment variable:
```bash
export P_PROFILE=dqn-adam
python print_params.py
```

## Parameter Layering
1. Configuration files (```.toml```, ```.yaml```, ```.ini```, ```.json```)
2. ```.env``` file (disabled by default)
3. Environment variables (default prefix 'P_')
4. Command-line arguments (via ```argparse```)
 
###
Overwrite parameter value:
```bash
python print_params.py --profile dqn-adam --lr 0.0002
```

## Devalopment stages profiles
Here is an example of using profiles to manage software development stages.

```toml
[default]
name = 'myapp'
debug = true
database_url = "mysql://devuser:devpass@localhost:3306/myapp"

[dev]
debug = true
database_url = "mysql://devuser:devpass@myapp-dev.example.com:3306/myapp_dev"

[test]
debug = false
database_url = "mysql://devuser:devpass@myapp-dev.example.com:3306/myapp_test"

[prod]
debug = false
database_url = "mysql://devuser:devpass@myapp.example.com:3306/myapp"
```

```bash
P_PROFILE=dev python myapp.py
```