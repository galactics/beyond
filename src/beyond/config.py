#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from configparser import ConfigParser


class ConfigError(AttributeError, KeyError):
    pass


class ConfigDict(dict):

    def __getitem__(self, name):
        if name not in self:
            raise ConfigError("Unknown configuration variable '%s'" % name)
        return super().__getitem__(name)

    def __getattr__(self, name):
        return self[name]

    def _get(self, key, default):
        return super().get(key, default)

    def get(self, section, value, default):
        """Retrieve a value in the config, if the value is not available
        give the default value specified.
        """

        out = self._get(section, default)

        if isinstance(out, ConfigDict):
            return out._get(value, default)
        else:
            return out


class Config(ConfigDict):
    """Configuration

    Example:
        .. code-block:: python

            from space.config import config
            print(config['env']['earth_orientation_source'])
            print(config.env.earth_orientation_source)
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def load(cls, path):
        """
        Args:
            path (pathlib.Path or str):
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        if path.is_file():
            # if the path provided is a conf file
            folder_path = path.parent
            conf_path = path
        else:
            folder_path = path
            conf_path = path / "beyond.conf"

        if not conf_path.exists():
            raise FileNotFoundError(conf_path)

        # reading of the conf file
        confparser = ConfigParser()
        confparser.read(str(conf_path))

        obj = cls()

        for section in confparser.sections():
            obj[section] = ConfigDict(confparser[section])

        obj['folder'] = folder_path


config = Config()
