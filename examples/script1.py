import json
import paramflow as pf

params = pf.load(path='script1.toml')
# params = pf.load()
print(json.dumps(params, indent=4))
