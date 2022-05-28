#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .registry import RegisteredFunction, Registry


try:
    from .version import __version__
except ImportError:
    __version__ = "Unknown"

__all__ = ["Registry", "RegisteredFunction"]
