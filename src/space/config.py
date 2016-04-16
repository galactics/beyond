#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path


class Config:
    
    _instance = None
    configfile = None

    def __new__(cls, *args, **kwargs):
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, configfile=None):

        if configfile is not None:
            configfile = Path(configfile)

            with configfile.open() as fh:
                for k, v in json.load(fh).items():
                    setattr(self, k, v)


try:
    config = Config(Path.cwd() / 'space.conf')
except FileNotFoundError:
    try:
        config = Config(Path.home() / ".space.conf")
    except FileNotFoundError:
        config = Config()



