import json
import paramflow as pf

# Example usages:
# P_FILE=params.toml python print_params.py
# P_FILE=params.yaml P_PROFILE=prod python print_params.py
# python print_params.py --sources params.yaml --profile=prod
# python print_params.py --sources params.toml
# python print_params.py --sources dqn_train.toml --profile dqn-adam
# python print_params.py --sources dqn_train.toml --profile dqn-adam --batch_size 64

params = pf.load()
print(json.dumps(params, indent=4))
