
import pytest

from beyond.config import config


@pytest.fixture(autouse=True)
def config_override(tmpdir):
    """Create a dummy config dict containing basic data
    """

    config.update({
        "eop": {
            "missing_policy": "pass",
        }
    })
