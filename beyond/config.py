#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Config(dict):
    """Configuration

    Example:
        .. code-block:: python

            from space.config import config

            print(config['env']['eop_missing_policy'])
            print(config.get('env', 'non-existant-field', fallback=25))

    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def get(self, *keys, fallback=None):
        """Retrieve a value in the config, if the value is not available
        give the fallback value specified.
        """

        section, *keys = keys
        out = super().get(section, fallback)

        while isinstance(out, dict):
            key = keys.pop(0)
            out = out.get(key, fallback)

        return out


config = Config()
