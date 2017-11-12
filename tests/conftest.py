
import pytest
from pathlib import Path

from beyond.config import config


@pytest.fixture(autouse=True)
def config_override(monkeypatch):
    """Override the config dictionnary
    """

    def mockget(*args):
        if args[:2] == ("env", "eop_missing_policy"):
            # Avoid errors when environement data are missing
            return "pass"
        else:
            return config.get(*args)

    def mockgetitem(name):
        print("yo")
        if name == "folder":
            return Path("/truc")
        else:
            return config.__getitem__(name)
    # monkeypatch.setattr("beyond.env.poleandtimes.config.get", mockget)
    monkeypatch.setattr("beyond.config.config.get", mockget)
    monkeypatch.setattr("beyond.config.config.__getitem__", mockgetitem)
