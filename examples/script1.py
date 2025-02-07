import json
import dparams as dp

params = dp.load('script1.toml')
print(json.dumps(params, indent=4))
