import picomamba


import json
from pathlib import Path
import pyjs
import shutil
import sysconfig
from itertools import chain
from functools import partial
from contextlib import contextmanager

import logging

logging.basicConfig(level=logging.DEBUG)


def callback(name, done, total):
    percent = 100.0 * done / total
    print(f"{name} {percent:.2f}% ({done}/{total})")


async def main():

    port = 8001
    dist_url = f"http://127.0.0.1:{port}"
    env_prefix = "/home/web_user/picomamba/env"

    arch_root_url = f"{dist_url}"

    arch_repodata_url = f"{dist_url}/arch_repodata_picomamba.tar.bz2"
    noarch_repodata_url = f"{dist_url}/noarch_repodata_picomamba.tar.bz2"

    noarch_template = (
        "https://beta.mamba.pm/get/conda-forge/noarch/{name}-{version}-{build}.tar.bz2"
    )
    pm = picomamba.PicoMamba(
        env_prefix=env_prefix,  # the name of the env
        arch_root_url=arch_root_url,  # root url for arch pkgs
        noarch_template=noarch_template,  # templated url for norach pkgs
        progress_callback=callback,  # report download progress
        use_indexded_db_cache=True,
    )
    await pm.initialize()
    await pm.fetch_repodata(
        arch_url=arch_repodata_url,  # url for arch repodata tar.bz2 file
        noarch_url=noarch_repodata_url,  # url for noarch repodata tar.bz2 file
    )
    print("fetch again")
    await pm.fetch_repodata(
        arch_url=arch_repodata_url,  # url for arch repodata tar.bz2 file
        noarch_url=noarch_repodata_url,  # url for noarch repodata tar.bz2 file
    )
    transaction = pm.solve(["regex", "sympy"])
    await pm.install_transaction(transaction)
    await pm.wait_for_emscripten()
    import regex

    print("rearchres:", regex.search("fo", "foo"))
