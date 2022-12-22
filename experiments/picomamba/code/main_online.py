import picomamba


from picomamba._picomamba import _PicoMambaCore, PicoMambaCoreSolveConfig

from picomamba.browser import (
    set_emscripten_module_locate_file_base_url,
    make_js_array,
    parallel_fetch_tarfiles,
    parallel_fetch_jsons,
    parallel_imports,
    make_js_func,
)
from picomamba.logging import logger, logged
from picomamba.tar import untar_to_temporary, untar_repodata
from picomamba.transaction import Transaction
from picomamba.conda_env import (
    ensure_is_conda_env,
    create_conda_meta,
)

import logging
import json
from pathlib import Path
import pyjs
import shutil
import sysconfig
from itertools import chain
from functools import partial
from contextlib import contextmanager


class PicoMamba(_PicoMambaCore):
    def __init__(
        self,
        env_prefix,
        repodata_dir,
        noarch_template,
        arch_root_url,
        side_path=None,
        progress_callback=None,
    ):
        super(PicoMamba, self).__init__()

        set_emscripten_module_locate_file_base_url(arch_root_url)

        self.progress_callback = progress_callback
        self.noarch_template = noarch_template
        self.arch_root_url = arch_root_url
        # where is the environment located
        self._env_prefix = Path(env_prefix)

        if side_path is None:
            self.side_path = Path(sysconfig.get_path("purelib"))
        else:
            self.side_path = Path(side_path)

        # where downloaded repo-data will be stored
        self._repodata_dir = Path(repodata_dir)

        # for progress bar
        self._progress = dict()

    def _register_installed_packages(self):
        # ensure that this is really a path to an env
        ensure_is_conda_env(self._env_prefix)
        with logged("load installed packages"):
            self._load_installed(str(self._env_prefix))

    def _load_repodata(self, repodata, filename, url):
        if isinstance(repodata, bytes):
            with open(filename, "wb") as f:
                f.write(repodata)
        else:
            with open(filename, "w") as f:
                json.dump(repodata, f)

        self._load_repodata_from_file(filename, url)

    async def fetch_repodata(self, arch_url, noarch_url):
        callback = None
        if self.progress_callback is not None:
            callback = partial(self.progress_callback, "repodata")

        with logged("download_repodata"):
            # download tarfiles which contain repodata as compressed json
            callback = [None, self.on_repodata_progress][
                self.progress_callback is not None
            ]
            tars = await parallel_fetch_tarfiles([arch_url, noarch_url], callback)

        with logged("untar repodata"):
            # untar and load repodata into libsolv
            for tar, repo_name in zip(tars, ["arch", "noarch"]):
                json_path = untar_repodata(tar, path=self._repodata_dir / repo_name)
                self._load_repodata_from_file(str(json_path), repo_name)

    def solve(self, specs, dry_run=False, pin_installed=False):

        # make libsolv aware of pkgs already
        # present in the environment
        self._register_installed_packages()

        with logged("solve"):
            config = PicoMambaCoreSolveConfig()
            raw_transaction = self._solve(specs, config)
            return Transaction(raw_transaction=raw_transaction)

    # this triggered from on_arch_progress and on_noarch_progress
    # and adds up both for a total progress bar
    def on_progress(self):
        downloaded = (
            self._progress["arch_downloaded"] + self._progress["noarch_downloaded"]
        )
        total = self._progress["arch_total"] + self._progress["noarch_total"]
        if self.progress_callback is not None:
            self.progress_callback("packages", downloaded, total)

    # this is called when we make progress on downloading arch packages
    def on_arch_progress(self, status, _, downloaded, total):
        self._progress["arch_downloaded"] = downloaded
        self._progress["arch_total"] = total
        self.on_progress()

    # this is called when we make progress on downloading noarch packages
    def on_noarch_progress(self, downloaded, total, finished_items, n_items):
        self._progress["noarch_downloaded"] = downloaded
        self._progress["noarch_total"] = total
        self.on_progress()

    # this is called when we make progress on downloading the repotdata
    def on_repodata_progress(self, downloaded, total, finished_items, n_items):
        if self.progress_callback is not None:
            self.progress_callback("repodata", downloaded, total)

    @contextmanager
    def _progress_reporting(self):

        last = [0.0]
        offset = [None]

        # we need to do a tiny hack and remove the
        # first reported "downloaded" since this
        # is what was already downloaded from
        # previous runs
        def progress_callback(downloaded, total):
            if offset[0] is None:
                offset[0] = downloaded
            downloaded -= offset[0]
            total -= offset[0]
            self.on_arch_progress(downloaded, total)

        js_on_progress, js_on_progress_handle = make_js_func(progress_callback)
        pyjs.js.globalThis.EmscriptenForgeModule.empackSetStatus = js_on_progress
        yield
        js_on_progress_handle.delete()

    async def install_transaction(self, transaction):
        self._progress = dict(
            arch_downloaded=0, arch_total=0, noarch_downloaded=0, noarch_total=0
        )

        with self._progress_reporting():
            logger.info("install transaction")

            # arch
            arch_promise = self.install_arch_packages(transaction.install["arch"])

            # noarch
            install_noarch = transaction.install["noarch"]
            tarfiles = await self.download_noarch_packages(install_noarch)
            self.install_noarch_packages(install_noarch, tarfiles)

            logger.info("wait for deps")
            await self.wait_for_emscripten()
            await arch_promise
            logger.info("done")

    def install_noarch_package(self, package, tar):
        with logged(f"install noarch {package}"):

            with untar_to_temporary(tar) as temp_dir:

                create_conda_meta(package=package, env_prefix=self._env_prefix)

                # copy side-packages
                if (temp_dir / "site-packages").is_dir():
                    shutil.copytree(
                        str(temp_dir / "site-packages"),
                        self.side_path,
                        dirs_exist_ok=True,
                    )

    async def install_arch_packages(self, packages):
        logger.info(f"install-arch {packages}")

        json_urls = [f"{self.arch_root_url}/{pkg.filename()}.json" for pkg in packages]

        urls = await parallel_fetch_jsons(json_urls)

        urls = [f"{self.arch_root_url}/{url}" for sublist in urls for url in sublist]

        await parallel_imports(urls)

    def install_noarch_packages(self, packages, tarfiles):
        for package, tar in zip(packages, tarfiles):
            self.install_noarch_package(package=package, tar=tar)
            tar.close()

    async def download_noarch_packages(self, packages):

        logger.info(f"install-noarch {packages}")
        urls = [pkg.format_url(self.noarch_template) for pkg in packages]
        callback = [None, self.on_noarch_progress][self.progress_callback is not None]
        return await parallel_fetch_tarfiles(urls, callback)

    async def wait_for_emscripten(self):
        await pyjs._module._wait_run_dependencies()


def callback(name, done, total):
    percent = 100.0 * done / total
    print(f"{name} {percent:.2f}% ({done}/{total})")


async def main():

    port = 8000
    dist_url = "http://picomamba-gra-emscripten-forge.auth-da651592c8a84c5ca1cf83deb28c741c.storage.gra.cloud.ovh.net"
    env_prefix = "/home/web_user/picomamba/env"
    repodata_dir = "/home/web_user"

    arch_root_url = f"{dist_url}"

    arch_repodata_url = f"{dist_url}/arch_repodata_picomamba.tar.bz2"
    noarch_repodata_url = f"{dist_url}/noarch_repodata_picomamba.tar.bz2"

    noarch_template = (
        "https://beta.mamba.pm/get/conda-forge/noarch/{name}-{version}-{build}.tar.bz2"
    )
    pm = PicoMamba(
        env_prefix=env_prefix,  # the name of the env
        repodata_dir=repodata_dir,  # where to store repodata
        arch_root_url=arch_root_url,  # root url for arch pkgs
        noarch_template=noarch_template,  # templated url for norach pkgs
        progress_callback=callback,  # report download progress
    )
    await pm.fetch_repodata(
        arch_url=arch_repodata_url,  # url for arch repodata tar.bz2 file
        noarch_url=noarch_repodata_url,  # url for noarch repodata tar.bz2 file
    )
    transaction = pm.solve(["regex"])
    await pm.install_transaction(transaction)

    import regex

    print("rearchres:", regex.search("fo", "foo"))
