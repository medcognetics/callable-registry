#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from registry import Registry


@pytest.mark.parametrize("name", ["name1", "name2"])
def test_construct(name):
    reg = Registry(name)
    assert reg.name == name
    assert len(reg) == 0


def test_repr():
    reg = Registry("name")
    s = str(reg)
    assert isinstance(s, str)


@pytest.mark.parametrize("func_name", ["func1", "func2"])
def test_register_class(func_name):
    reg = Registry("name")
    assert reg.name == "name"

    @reg(name=func_name)
    class DummyClass:
        pass

    assert func_name in reg
    assert reg.get(func_name) is DummyClass


@pytest.mark.parametrize("func_name", ["func1", "func2"])
def test_register_function(func_name):
    reg = Registry("name")

    def func():
        pass

    reg(func, name=func_name)
    assert func_name in reg
    assert reg.get(func_name) is func


@pytest.mark.parametrize("func_name", ["func1", "func2"])
def test_contains(func_name):
    reg = Registry("name")

    @reg(name=func_name)
    class DummyClass:
        pass

    assert func_name in reg


@pytest.mark.parametrize("length", [0, 1, 2])
def test_length(length):
    reg = Registry("name")

    def func():
        pass

    for i in range(length):
        reg(func, name=f"func-{i}")
    assert len(reg) == length


def test_get_with_metadata():
    reg = Registry("name")
    metadata = dict(data1="1", data2="2")

    name = "func"

    @reg(name=name, **metadata)
    class DummyClass:
        pass

    result = reg.get_with_metadata(name)
    assert result.fn is DummyClass
    assert result.name == name
    assert result.metadata == metadata


@pytest.mark.parametrize(
    "names",
    [
        ("f1",),
        ("f1", "f2"),
    ],
)
def test_available_keys(names):
    reg = Registry("name")

    def func():
        pass

    for name in names:
        reg(func, name=name)
    assert reg.available_keys() == sorted(names)
