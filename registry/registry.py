#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field, replace
from functools import partial
from inspect import signature
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Type, TypeVar, Union, cast


try:
    from typing import ParamSpec  # pragma: no cover
except ImportError:
    from typing_extensions import ParamSpec  # pragma: no cover

try:
    from typing import Self  # pragma: no cover
except ImportError:
    from typing_extensions import Self  # pragma: no cover


T = TypeVar("T")
U = TypeVar("U")
F = TypeVar("F", bound="RegisteredFunction")
P = ParamSpec("P")

P_cast = ParamSpec("P_cast")
T_cast = TypeVar("T_cast")

C = Union[Callable[P, T], Type[Callable[P, T]]]

_REGISTERED_FUNCTION = Dict[str, Any]


def iterate_arg_names(func: Callable) -> Iterator[str]:
    r"""Iterates over the arg names of a callable"""
    sig = signature(func)
    for name, param in sig.parameters.items():
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            yield name


def has_var_kwargs(func: Callable) -> bool:
    r"""Check if a callable supports **kwargs"""
    sig = signature(func)
    return any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())


def bind_relevant_kwargs(func: Callable[..., T], **kwargs) -> Callable[..., T]:
    r"""Binds keyword args to a callable"""
    if not kwargs:
        return func

    # edge case to handle signature hidden in a functools.partial
    if isinstance(func, partial):
        return bind_relevant_kwargs(func.func, **{**func.keywords, **kwargs})

    # for a function with **kwargs, we can bind everything
    if has_var_kwargs(func):
        return partial(func, **kwargs)

    # for functions without **kwargs, only bind kwargs that appear in function signature
    arg_names = set(iterate_arg_names(func))
    kwargs_to_bind = {k: v for k, v in kwargs.items() if k in arg_names}
    return partial(func, **kwargs_to_bind)


@dataclass(frozen=True)
class RegisteredFunction(Generic[P, T]):
    fn: Callable[P, T]
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_type(self) -> bool:
        r"""Checks if ``fn`` is a type"""
        if isinstance(self.fn, partial):
            return isinstance(self.fn.func, type)
        return isinstance(self.fn, type)

    def instantiate(self, **kwargs) -> "RegisteredFunction":
        if self.is_type:
            fn = bind_relevant_kwargs(self.fn, **kwargs)()
            return replace(self, fn=fn)
        return self

    def instantiate_with_metadata(self, **kwargs) -> "RegisteredFunction":
        kwargs = {**self.metadata, **kwargs}
        return self.instantiate(**kwargs)

    def cast(self, typ: Type[Callable[P_cast, T_cast]]) -> "RegisteredFunction[P_cast, T_cast]":
        return self  # type: ignore

    def bind(self: Self, **kwargs) -> "RegisteredFunction":
        return replace(self, fn=bind_relevant_kwargs(self.fn, **kwargs))

    def bind_metadata(self: Self, **kwargs) -> "RegisteredFunction":
        kwargs = {**self.metadata, **kwargs}
        return self.bind(**kwargs)

    def __call__(self: Self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.fn(*args, **kwargs)


class Registry(Generic[P, T]):
    """A registry is used to register callables and associated metadata under a string name for easy access.

    Modeled after https://github.com/PyTorchLightning/lightning-flash/flash/core/registry.py

    Args:
        name: Name of the registry
        bind_metadata: If ``True``, treat metadata as keyword args that will be bound using :func:`functools.partial`
        bound: A callable from which to bind generic type variables. Used only for type checking.
    """

    def __init__(
        self,
        name: str,
        bound: Optional[Type[Callable[P, T]]] = None,
    ) -> None:
        self.name = name
        self.functions: Dict[str, RegisteredFunction[P, T]] = {}

    def __len__(self) -> int:
        return len(self.functions)

    def __contains__(self, key: Any) -> bool:
        return any(key == e.name for e in self.functions.values())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, " f"functions={self.functions.keys()})"

    def get(self, key: Union[str, Callable[P, T]]) -> RegisteredFunction[P, T]:
        if isinstance(key, str):
            if key not in self:
                raise KeyError(f"Key: {key} is not in {type(self).__name__}. Available keys: {self.available_keys()}")
            result = self.functions[key]
        elif callable(key):
            result = RegisteredFunction(key, "", {})
        else:
            raise TypeError(f"`key` should be str or callable, found {type(key)}")  # pragma: no cover
        return cast(RegisteredFunction[P, T], result)

    def remove(self, key: str) -> None:
        self.functions.pop(key)

    def _register_function(
        self,
        fn: Callable[P, T],
        name: Optional[str] = None,
        override: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not callable(fn):
            raise TypeError(f"You can only register a callable, found: {fn}")  # pragma: no cover

        if name is None:
            if hasattr(fn, "func"):
                name = fn.func.__name__
            else:
                name = fn.__name__
        assert isinstance(name, str)

        item: RegisteredFunction[P, T] = RegisteredFunction(fn, name, metadata or {})  # type: ignore

        if override and name in self:
            raise RuntimeError(  # pragma: no cover
                f"Function with name: {name} and metadata: {metadata} is already present within {self}."
                " HINT: Use `override=True`."
            )

        self.functions[name] = item

    def __call__(
        self,
        fn: Optional[Callable[P, T]] = None,
        name: Optional[str] = None,
        override: bool = False,
        **metadata,
    ) -> Callable:
        """This function is used to register new functions to the registry along their metadata.
        Functions can be filtered using metadata using the ``get`` function.
        """
        if fn is not None:
            self._register_function(fn=fn, name=name, override=override, metadata=metadata)
            return fn

        # raise the error ahead of time
        if not (name is None or isinstance(name, str)):
            raise TypeError(f"`name` must be a str, found {name}")  # pragma: no cover

        def _register(cls):
            self._register_function(fn=cls, name=name, override=override, metadata=metadata)
            return cls

        return _register

    def available_keys(self) -> List[str]:
        return sorted(self.functions.keys())

    def register_dict(self, fn_dict: Dict[str, Callable[P, T]], override: bool = False) -> None:
        r"""Register a dictionary of functions. The keys of the dictionary will be used as the name of the function.

        Args:
            fn_dict: A dictionary of functions to register.
            override: If ``True``, override existing functions.
        """
        for name, fn in fn_dict.items():
            self(fn=fn, name=name, override=override)
