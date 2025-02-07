import json
import dparams as dp

# params = dp.load('script1.toml')
params = dp.load()
print(json.dumps(params, indent=4))
