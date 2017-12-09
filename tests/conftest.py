
import pytest
from pathlib import Path

from beyond.config import config


@pytest.fixture(autouse=True)
def config_override(tmpdir):
    """Create a dummy config file containing basic data
    """

    config.update({
        "env": {
            "folder": Path(str(tmpdir))
        },
        "eop": {
            "missing_policy": "pass",
        }
    })
