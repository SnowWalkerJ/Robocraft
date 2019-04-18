import os

import yaml


__path = os.path.join(os.path.dirname(__file__), "config.yml")
with open(__path, "r") as f:
    CONFIG = yaml.safe_load(f)
