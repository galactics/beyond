
import pytest
from pathlib import Path

from beyond.config import config


@pytest.fixture(autouse=True)
def config_override(tmpdir):
    """Create a dummy config file containing basic data
    """

    config.update({
        "env": {
            "eop_missing_policy": "pass",
            "folder": Path(str(tmpdir))
        }
    })
