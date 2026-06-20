"""Put tools/ on the import path and provide HTTP test doubles."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))


class Resp:
    """Minimal stand-in for a requests.Response."""

    def __init__(self, status=200, data=None, text=""):
        self.status_code = status
        self._data = {} if data is None else data
        self.text = text

    def json(self):
        return self._data
