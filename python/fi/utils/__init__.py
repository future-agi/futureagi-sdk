from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("futureagi")
except PackageNotFoundError:
    __version__ = "0.6.13"
__versions__ = __version__
