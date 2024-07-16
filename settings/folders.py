import os
from os.path import dirname
from pathlib import Path

# Filesystem paths
BASE_PATH = Path(os.path.abspath(dirname(dirname(__file__))))
DATA_PATH = BASE_PATH / "data"
SPOT_DATA_PATH = DATA_PATH /"spot"
DAILY_KLINES = SPOT_DATA_PATH / "daily" / "klines"
MONTHLY_KLINES = SPOT_DATA_PATH / "monthly" / "klines"
SETTINGS_PATH = BASE_PATH / "settings"
TEST_PATH = BASE_PATH / "tests"
