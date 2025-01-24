import os
import socket
from pathlib import Path

import pytest

from empack.file_patterns import pkg_file_filter_from_yaml
from empack.pack import DEFAULT_CONFIG_PATH

CONFIG_PATH = DEFAULT_CONFIG_PATH
FILE_FILTERS = pkg_file_filter_from_yaml(CONFIG_PATH)
CHANNELS = ["conda-forge", "https://repo.mamba.pm/emscripten-forge"]


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="function")
def free_port():
    return get_free_port()


@pytest.fixture(scope="module")
def tmp_path_module(request, tmpdir_factory):
    """A tmpdir fixture for the module scope. Persists throughout the module."""
    return Path(tmpdir_factory.mktemp(request.module.__name__))
