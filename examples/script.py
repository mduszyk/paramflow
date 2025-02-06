import json

import dparams as dp


params = dp.load('params.toml')
print(json.dumps(params, indent=4))
