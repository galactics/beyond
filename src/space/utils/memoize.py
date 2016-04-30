#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools


def memoize(obj):
    """Memoize decorator, as seen on
    `here <https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize>`_
    """
    cache = obj._cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer
