#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from configparser import ConfigParser


class Config:
    """Configuration class

    The class has no real interest in itself. You should use the ``config``
    instance variable.

    Example:

    .. code-block:: python

        from space.config import config
        config.load("/home/user/project-X/data")

        print(config['env']['pole_motion_source'])  # 'all'
    """

    _instance = None
    folder = None

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, folder=None):
        if folder is not None:
            self.load(folder)

    def load(self, folder):
        """Set a folder as configuration source.

        Args:
            folder (:py:class:`pathlib.Path` or :py:class:`str`)
        """
        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(folder)

        self.folder = folder

        confpath = self.folder / "space.conf"

        self._conf = ConfigParser()
        self._conf.read(str(confpath))

    def __getitem__(self, item):
        return dict(self._conf[item])

try:
    # Load the '~/.space' folder
    config = Config(Path.home() / ".space")
except FileNotFoundError:
    # If it doesn't exist, use an empty config instance
    config = Config()
