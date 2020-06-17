"""Top-level package for Django Prepared Properties."""

__author__ = """Robin Ramael"""
__email__ = "robin.ramael@gmail.com"
__version__ = "1.0.1"

from .prepared_properties import (
    AnnotatedProperty,
    PrefetchedProperty,
    PropertiedQueryset,
    annotated_property,
)

__all__ = [
    "AnnotatedProperty",
    "annotated_property",
    "PrefetchedProperty",
    "PropertiedQueryset",
]
