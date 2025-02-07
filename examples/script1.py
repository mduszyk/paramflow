import json
import paramflow as pf

# params = dp.load('script1.toml')
params = pf.load()
print(json.dumps(params, indent=4))
