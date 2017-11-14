#!/usr/bin/env python
# -*- coding: utf-8 -*-

import toml
from pathlib import Path


class Config(dict):
    """Configuration

    Example:
        .. code-block:: python

            from space.config import config
            print(config['env']['eop_missing_policy'])
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def get(self, section, value, fallback):
        """Retrieve a value in the config, if the value is not available
        give the fallback value specified.
        """

        out = super().get(section, fallback)

        if isinstance(out, dict):
            return out.get(value, fallback)
        else:
            return out

    @property
    def folder(self):
        return self['folder']

    def read(self, filepath):
        """Read the config file and load it in memory

        Args:
            filepath (pathlib.Path or str)
        Raises:
            FileNotFoundError
        """

        filepath = Path(filepath)

        self.clear()
        self['folder'] = filepath.parent

        self.update(toml.load(str(filepath)))


config = Config()
