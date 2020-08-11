from pytest import raises
from beyond.config import config, ConfigError


def test_get():

    assert config.get("eop", "missing_policy") == "pass"
    assert config.get("dummy1", "dummy2") is None
    assert config.get("dummy1", "dummy2", fallback=False) == False
    assert config.get("dummy1", "dummy2", fallback="hello") == "hello"

    with raises(ConfigError):
        config.get("eop", "missing_policy", "dummy")


def test_set():

    config.set("dummy1", "dummy2", "test")
    assert config["dummy1"]["dummy2"] == "test"
    assert config.get("dummy1", "dummy2") == "test"
