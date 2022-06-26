#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable

import pytest

from registry import RegisteredFunction, Registry


@dataclass
class CallableClass:
    foo: int = 1

    def __call__(self, *args, **kwargs):
        ...


@dataclass
class CallableClassWithArg:
    foo: int = 1

    def __call__(self, x: int):
        return x


def dummy_func(*args, **kwargs):
    ...


class TestRegisteredFunction:
    def test_call(self):
        fn = CallableClassWithArg()
        func = RegisteredFunction(fn, "foo")
        assert func(x=1) == 1

    @pytest.mark.parametrize(
        "fn,exp",
        [
            pytest.param(dummy_func, False),
            pytest.param(str, True),
            pytest.param(CallableClass, True),
            pytest.param(CallableClass(), False),
        ],
    )
    def test_is_type(self, fn, exp):
        func = RegisteredFunction(fn, "foo")
        assert func.is_type == exp

    @pytest.mark.parametrize(
        "fn,exp",
        [
            pytest.param(dummy_func, dummy_func),
            pytest.param(CallableClass, CallableClass()),
            pytest.param(CallableClass(), CallableClass()),
        ],
    )
    def test_instantiate(self, fn, exp):
        func = RegisteredFunction(fn, "foo")
        inst = func.instantiate(bar="bar")
        assert inst.fn == exp

    @pytest.mark.parametrize(
        "fn,exp",
        [
            pytest.param(dummy_func, dummy_func),
            pytest.param(CallableClass, CallableClass(foo=2)),
            pytest.param(CallableClass(), CallableClass()),
        ],
    )
    def test_instantiate_with_metadata(self, fn, exp):
        func = RegisteredFunction(fn, "foo", {"foo": 2})
        inst = func.instantiate_with_metadata(bar="bar")
        assert inst.fn == exp

    def test_cast(self):
        fn = CallableClass()
        func = RegisteredFunction(fn, "foo")
        casted_func = func.cast(Callable[[int], int])
        assert casted_func == func

    def test_bind(self):
        fn = CallableClassWithArg()
        func = RegisteredFunction(fn, "foo")
        bound = func.bind(x=1, y=2)
        assert bound() == 1

    def test_bind_with_metadata(self):
        fn = CallableClassWithArg()
        func = RegisteredFunction(fn, "foo", {"x": 1})
        bound = func.bind_metadata(y=2)
        assert bound() == 1


class TestRegistry:
    @pytest.mark.parametrize("name", ["name1", "name2"])
    def test_construct(self, name):
        reg = Registry(name)
        assert reg.name == name
        assert len(reg) == 0

    def test_repr(self):
        reg = Registry("name")
        s = str(reg)
        assert isinstance(s, str)

    @pytest.mark.parametrize("func_name", ["func1", "func2"])
    def test_register_class(self, func_name):
        reg = Registry("name")
        assert reg.name == "name"

        @reg(name=func_name)
        class DummyClass:
            pass

        assert func_name in reg
        assert reg.get(func_name).fn is DummyClass

    @pytest.mark.parametrize("func_name", ["func1", "func2"])
    def test_register_function(self, func_name):
        reg = Registry("name")

        def func(x: int) -> None:
            pass

        reg(func, name=func_name)
        assert func_name in reg
        assert reg.get(func_name).fn is func

    @pytest.mark.parametrize("func_name", ["func1", "func2"])
    def test_contains(self, func_name):
        reg = Registry("name")

        @reg(name=func_name)
        class DummyClass:
            pass

        assert func_name in reg

    @pytest.mark.parametrize("length", [0, 1, 2])
    def test_length(self, length):
        reg = Registry("name")

        def func():
            pass

        for i in range(length):
            reg(func, name=f"func-{i}")
        assert len(reg) == length

    @pytest.mark.parametrize(
        "names",
        [
            ("f1",),
            ("f1", "f2"),
        ],
    )
    def test_available_keys(self, names):
        reg = Registry("name")

        def func():
            pass

        for name in names:
            reg(func, name=name)
        assert reg.available_keys() == sorted(names)

    def test_type_annotation(self):
        def func(x: int, y: int) -> float:
            return float(x + y)

        reg = Registry("name", bound=Callable[[int, int], float])
        reg(func, name="func")
        x = reg.get("func")
        assert x(1, 2) == float(3)
