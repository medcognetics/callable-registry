#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Callable, List

from registry import Registry


STRING_REGISTRY = Registry("string", bound=Callable[[str], str])


@STRING_REGISTRY(name="strip")
def strip(x: str) -> str:
    return x.strip()


@STRING_REGISTRY(name="getword-0", index=0)
@STRING_REGISTRY(name="getword-1", index=1)
@dataclass
class GetWord:
    index: int = 0

    def __call__(self, x: str, **kwargs) -> str:
        return x.split(" ")[self.index]


def to_upper(x: str) -> str:
    return x.upper()


lines = [
    " nuke the site from orbit...",
    "only way to be sure ",
]


pipeline = ["strip", "getword-1", to_upper]


output_lines: List[str] = []
for line in lines:
    for step in pipeline:
        fn = STRING_REGISTRY.get(step).instantiate_with_metadata()
        line = fn(line)
    output_lines.append(line)

# should output ["THE", "WAY"]
print(output_lines)
