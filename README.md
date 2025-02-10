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
params = pf.load(file='params.toml')
print(params.learning_rate)
```

### Metaparameter Layering (Controls paramflow.load)
1. ```paramflow.load(...)``` arguments
2. Environment variables
3. Command-line arguments (via argparse)

## Parameter Layering
1. Configuration files (```.toml```, ```.yaml```, ```.ini```, ```.json```)
2. ```.env``` file (disabled by default)
3. Environment variables (with a specified prefix)
4. Command-line arguments (via ```argparse```)
 