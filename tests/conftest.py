
import toml
import pytest

from beyond.config import config


@pytest.fixture(autouse=True)
def config_override(tmpdir):
    """Create a dummy config file containing basic data
    """

    p = tmpdir.join("beyond.conf")
    p.write(toml.dumps({"env": {"eop_missing_policy": "pass"}}))
    config.read(p)
