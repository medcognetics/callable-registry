#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, Generic, List, Optional, ParamSpec, TypeVar, cast


T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")

_REGISTERED_FUNCTION = Dict[str, Any]


@dataclass
class RegisteredFunction(Generic[P, T]):
    fn: Callable[P, T]
    name: str
    metadata: Dict[str, Any]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.fn(*args, **kwargs)


class Registry(Generic[P, T]):
    """A registry is used to register callables and associated metadata under a string name for easy access.

    Modeled after https://github.com/PyTorchLightning/lightning-flash/flash/core/registry.py

    Args:
        name: Name of the registry
        bind_metadata: If ``True``, treat metadata as keyword args that will be bound using :func:`functools.partial`
        bound: A callable from which to bind generic type variables. Used only for type checking.
    """

    def __init__(self, name: str, bind_metadata: bool = False, bound: Optional[Callable[P, T]] = None) -> None:
        self.name = name
        self.functions: Dict[str, RegisteredFunction[P, T]] = {}
        self.bind_metadata = bind_metadata

    def __len__(self) -> int:
        return len(self.functions)

    def __contains__(self, key: Any) -> bool:
        return any(key == e.name for e in self.functions.values())

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name}, "
            f"bind_metadata={self.bind_metadata}, "
            f"functions={self.functions.keys()})"
        )

    def get(self, key: str, **kwargs) -> Callable[P, T]:
        item = self.get_with_metadata(key)
        fn = cast(Callable[P, T], item.fn)
        metadata = item.metadata
        if self.bind_metadata:
            kwargs = {**metadata, **kwargs}
        return partial(fn, **kwargs) if kwargs else fn

    def get_with_metadata(self, key: str) -> RegisteredFunction[P, T]:
        if key not in self:
            raise KeyError(f"Key: {key} is not in {type(self).__name__}. Available keys: {self.available_keys()}")
        return self.functions[key]

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
            raise TypeError(f"You can only register a callable, found: {fn}")

        if name is None:
            if hasattr(fn, "func"):
                name = fn.func.__name__
            else:
                name = fn.__name__
        assert isinstance(name, str)

        item: RegisteredFunction[P, T] = RegisteredFunction(fn, name, metadata or {})  # type: ignore

        if override and name in self:
            raise RuntimeError(
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
            raise TypeError(f"`name` must be a str, found {name}")

        def _register(cls):
            self._register_function(fn=cls, name=name, override=override, metadata=metadata)
            return cls

        return _register

    def available_keys(self) -> List[str]:
        return sorted(self.functions.keys())
