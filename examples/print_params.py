import json
import paramflow as pf

params = pf.load()
print(json.dumps(params, indent=4))
