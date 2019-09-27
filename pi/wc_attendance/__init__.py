__version__ = "0.0.1-DEV"

import logging

from .data_store import Person, DataStore, CardUid, UnixTime
from .json_store import JsonFileStore

root = logging.getLogger(__name__)
root.setLevel(logging.DEBUG)

__all__ = ['Person', 'DataStore', 'CardUid', 'UnixTime', 'JsonFileStore']
