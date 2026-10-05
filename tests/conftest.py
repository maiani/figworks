"""Shared test helpers."""

from __future__ import annotations

import re
from collections.abc import Callable

import numpy as np
import pytest
from lxml import etree


def _ctm(node: etree._Element) -> np.ndarray:
    """The affine map from ``node``'s user units to document px."""
    m = np.eye(3)
    chain = [node, *node.iterancestors()]
    for current in reversed(chain):
        for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", current.get("transform", "")):
            v = [float(x) for x in args.replace(",", " ").split()]
            if name == "translate":
                step = np.array([[1, 0, v[0]], [0, 1, v[1] if len(v) > 1 else 0], [0, 0, 1]])
            elif name == "scale":
                sy = v[1] if len(v) > 1 else v[0]
                step = np.diag([v[0], sy, 1.0])
            elif name == "matrix":
                step = np.array([[v[0], v[2], v[4]], [v[1], v[3], v[5]], [0, 0, 1]])
            else:
                raise AssertionError(f"unexpected transform {name}")
            m = m @ step
    return m


@pytest.fixture
def ctm() -> Callable[[etree._Element], np.ndarray]:
    """Independent of FigWorks's own transform handling, so it can check it."""
    return _ctm
