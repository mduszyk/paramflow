# paramflow
Parameter/configuration library motivated by the usecase of training ML models
with multple sets of hyperparameters (profiles). The goal is to make it easy to
use and flexible. Generate cmd arg parser based on the params from the firs file.
Allow for easy owerwriting of params.

## Features:
- layered parameters (files, environment, cmd args)
- python frozen dictionary with attribute access
- support for parameter profiles
- metaparameters also layered (parameters to paramflow load)

```python
import paramflow as pf
params = pf.load('params.toml')
```

## Metaparameters
Parameters to ```paramflow.load``` can be layered too.

### Metaparameters Layereing
1. ```paramflow.load``` function arguments
2. environment variables
3. argparse

## Parameters Layereing
1. Files (toml, yaml, ini, json)
2. ```.env``` file (disabled by default)
3. Environment (env vars with a prefix)
4. argparse
