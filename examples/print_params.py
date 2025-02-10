import json
import paramflow as pf

# Example usages:
# P_FILE=params.toml python print_params.py
# P_FILE=params.yaml P_PROFILE=prod python print_params.py
# python print_params.py --file params.yaml --profile=prod
# python print_params.py --file params.toml
# python print_params.py --file dqn_params.toml --profile dqn-adam
# python print_params.py --file dqn_params.toml --profile dqn-adam --batch_size 64

params = pf.load()
print(json.dumps(params, indent=4))
