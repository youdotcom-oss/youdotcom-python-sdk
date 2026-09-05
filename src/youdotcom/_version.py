
import importlib.metadata

__title__: str = "youdotcom"
__version__: str = "3.3.0"
__openapi_doc_version__: str = "1.0.0"

try:
    if __package__ is not None:
        __version__ = importlib.metadata.version(__package__)
except importlib.metadata.PackageNotFoundError:
    pass

__user_agent__: str = f"youdotcom-python-sdk/{__version__}"
