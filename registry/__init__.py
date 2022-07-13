#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .registry import RegisteredFunction, Registry, bind_relevant_kwargs, has_var_kwargs, iterate_arg_names


try:
    from .version import __version__
except ImportError:
    __version__ = "Unknown"

__all__ = ["Registry", "RegisteredFunction", "iterate_arg_names", "has_var_kwargs", "bind_relevant_kwargs"]
