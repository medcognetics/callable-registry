#!/usr/bin/env python
# -*- coding: utf-8 -*-
import importlib.metadata

from .registry import RegisteredFunction, Registry, bind_relevant_kwargs, has_var_kwargs, iterate_arg_names


__version__ = importlib.metadata.version("callable-registry")

__all__ = ["Registry", "RegisteredFunction", "iterate_arg_names", "has_var_kwargs", "bind_relevant_kwargs"]
