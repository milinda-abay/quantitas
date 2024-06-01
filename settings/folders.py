import os
from os.path import dirname
from pathlib import Path

# Filesystem paths
BASE_PATH = Path(os.path.abspath(dirname(dirname(__file__))))
DATA_PATH = BASE_PATH / "data"
INPUT_PATH = DATA_PATH / "input"
SETTINGS_PATH = BASE_PATH / "settings"
TEST_PATH = BASE_PATH / "tests"
