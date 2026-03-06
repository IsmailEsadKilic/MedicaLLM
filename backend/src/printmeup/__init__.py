"""
printmeup - A colorful terminal printing utility package.

Provides functions for printing formatted, colored messages to the terminal with emojis for different message types.
"""

from .printmeup import (
    colors,
    deb,
    err,
    inf,
    war,
    suc,
    ins,
    rep,
    inp,
    rin,
    cull_long_string,
    try_all_colors,
    try_all_methods,
)

__all__ = [
    "colors",
    "deb",
    "err",
    "inf",
    "war",
    "suc",
    "ins",
    "rep",
    "inp",
    "rin",
    "try_all_colors",
    "try_all_methods",
    "cull_long_string",
]

__version__ = "0.1.0"
