"""SMAIRT: Scientific Method with AI Research Toolkit."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("smairt")
except PackageNotFoundError:
    __version__ = "0.2.0b1"

__all__ = ["__version__"]
