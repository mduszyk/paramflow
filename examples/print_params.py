import json
import paramflow as pf

# by default load params.toml
params = pf.load(file='params.toml')
print(json.dumps(params, indent=4))
