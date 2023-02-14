import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath
from typing import Union, List
from urllib import request

from appdirs import user_cache_dir
import requests
import typer

from .toposort import toposort

from .extend_js import extend_js
from .file_patterns import PkgFileFilter, pkg_file_filter_from_yaml
from .filter_env import filter_env, iterate_env_pkg_meta, split_filter_pkg

EMSDK_VER = "3.1.27"
EMSDK_INSTALL_PATH = Path(user_cache_dir("empack"))
DEFAULT_CONFIG_PATH = Path(sys.prefix) / "share" / "empack" / "empack_config.yaml"


def download_and_setup_emsdk(emsdk_version=None):
    emsdk_version = EMSDK_VER if emsdk_version is None else emsdk_version

    emsdk_dir = f"emsdk-{emsdk_version}"

    file_packager_path = (
        EMSDK_INSTALL_PATH
        / emsdk_dir
        / "upstream"
        / "emscripten"
        / "tools"
        / "file_packager.py"
    )

    EMSDK_INSTALL_PATH.mkdir(parents=True, exist_ok=True)

    if not os.path.isdir(EMSDK_INSTALL_PATH / emsdk_dir):
        file = f"{emsdk_version}.zip"
        request.urlretrieve(
            f"https://github.com/emscripten-core/emsdk/archive/refs/tags/{file}",
            EMSDK_INSTALL_PATH / file,
        )
        shutil.unpack_archive(EMSDK_INSTALL_PATH / file, EMSDK_INSTALL_PATH)
        os.rename(
            EMSDK_INSTALL_PATH / f"emsdk-{emsdk_version}",
            EMSDK_INSTALL_PATH / emsdk_dir,
        )
        os.remove(EMSDK_INSTALL_PATH / file)

        subprocess.run(
            [
                sys.executable,
                str(EMSDK_INSTALL_PATH / emsdk_dir / "emsdk.py"),
                "install",
                emsdk_version,
            ],
            shell=False,
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(EMSDK_INSTALL_PATH / emsdk_dir / "emsdk.py"),
                "activate",
                emsdk_version,
            ],
            shell=False,
            check=True,
        )

        for _file in [
            "emsdk",
            Path("upstream") / "emscripten" / "emcc",
            Path("upstream") / "emscripten" / "emar",
            Path("upstream") / "emscripten" / "em++",
        ]:
            _exec = str(EMSDK_INSTALL_PATH / emsdk_dir / _file)

            st = os.stat(_exec)
            os.chmod(_exec, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    assert os.path.exists(file_packager_path)

    return file_packager_path


# wrapper around the raw emscripten file packager
def emscripten_file_packager(
    outname: str,
    to_mount: str,
    mount_path: str,
    export_name: str,
    use_preload_plugins: bool = True,
    no_node: bool = True,
    lz4: bool = True,
    cwd=None,
    silent=False,
    emsdk_version=None,
):
    file_packager_path = download_and_setup_emsdk(emsdk_version)

    cmd = [
        sys.executable,
        str(file_packager_path),
        f"{outname}.data",
        "--preload",
        f"{to_mount}@{mount_path}",
        f"--js-output={outname}.js",
        f"--export-name={export_name}",
    ]
    if use_preload_plugins:
        cmd += ["--use-preload-plugins"]

    if no_node:
        cmd += ["--no-node"]

    if lz4:
        cmd += ["--lz4"]
    try:
        if not silent:
            res = subprocess.check_output(
                cmd, shell=False, cwd=cwd, stderr=subprocess.STDOUT
            )
            print(res.decode("utf-8"))
        else:
            subprocess.run(
                cmd,
                shell=False,
                check=True,
                cwd=cwd,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
    except subprocess.CalledProcessError as e:
        print(e.output.decode("utf-8"))
        raise e


def split_pack_environment(
    env_prefix: Path,
    outname: str,
    export_name: str,
    with_export_default_statement=False,
    pkg_file_filter: Union[PkgFileFilter, None] = None,
    pack_outdir: Union[str, None] = None,
    emsdk_version: Union[str, None] = None,
    silent: bool = False,
):
    if pack_outdir is None:
        pack_outdir = os.getcwd()

    if pkg_file_filter is None:
        pkg_file_filter = pkg_file_filter_from_yaml(DEFAULT_CONFIG_PATH)

    # name of the env
    env_name = PurePath(env_prefix).parts[-1]
    js_files = []
    pkg_metas = list(iterate_env_pkg_meta(env_prefix))
    pkg_metas = toposort(pkg_metas)
    for pkg_meta in pkg_metas:

        pkg_outname = pkg_meta["fn"][:-8]
        pkg_name = pkg_meta["name"]

        matchers = pkg_file_filter.get_matchers(pkg_name=pkg_name)

        with tempfile.TemporaryDirectory() as temp_root_dir:

            temp_dirs = []
            target_dirs = []
            for i in range(len(matchers)):
                temp_dir = os.path.join(temp_root_dir, f"{i}")
                target_dir = os.path.join(temp_dir, env_name)
                os.makedirs(target_dir)
                temp_dirs.append(temp_dir)
                target_dirs.append(target_dir)

            has_any_files = split_filter_pkg(
                env_prefix=env_prefix,
                pkg_meta=pkg_meta,
                target_dirs=target_dirs,
                matchers=matchers,
            )

            for i in range(len(matchers)):
                if has_any_files[i]:
                    emscripten_file_packager(
                        outname=f"{pkg_outname}.{i}",
                        to_mount=env_name,
                        mount_path=env_prefix,
                        export_name=export_name,
                        use_preload_plugins=True,
                        no_node=export_name.startswith("globalThis"),
                        lz4=True,
                        cwd=str(temp_dirs[i]),
                        emsdk_version=emsdk_version,
                        silent=silent,
                    )
                    js_files.append(f"{pkg_outname}.{i}.js")
                    shutil.copy(
                        os.path.join(str(temp_dirs[i]), f"{pkg_outname}.{i}.data"),
                        pack_outdir,
                    )
                    shutil.copy(
                        os.path.join(str(temp_dirs[i]), f"{pkg_outname}.{i}.js"),
                        pack_outdir,
                    )

                    extend_js(os.path.join(pack_outdir, f"{pkg_outname}.{i}.js"))

    # Create the base js file, we either use importScripts if it's available (web worker)
    # or dynamic import if it's not
    # We cannot always use dynamic imports, as they are not available yet on Firefox web workers
    lines = ["if (typeof importScripts !== 'undefined') {"]

    for js_file in js_files:
        lines.append(f"importScripts('./{js_file}')")
        lines.append(f"await {export_name}._wait_run_dependencies()")

    lines.append("} else {")

    for js_file in js_files:
        lines.append(f"await import('./{js_file}')")
        lines.append(f"await {export_name}._wait_run_dependencies()")

    lines.append("}")

    function_body = "\n".join(lines)


    # browser
    if export_name.startswith("globalThis"):
        if with_export_default_statement:
            js_function_source = f"""export default async function(){{
                {function_body}
            }}
            """
        else:
            js_function_source = f"""async function importPackages(){{
                {function_body}
            }}
            {export_name}.importPackages = importPackages;
            """
    # node
    else:

        js_function_source = f"""async function importPackages(){{
            {function_body}
        }}
        module.exports = importPackages;
        """

    with open(os.path.join(pack_outdir, f"{outname}.js"), "w") as f:
        f.write(js_function_source)


def pack_repodata(
    repodata: dict,
    env_prefix: Path,
    channels: List,
    export_name: str,
    pkg_file_filter: Union[PkgFileFilter, None] = None,
    pack_outdir: Union[str, None] = None,
    emsdk_version: Union[str, None] = None,
):
    if pack_outdir is None:
        pack_outdir = os.getcwd()

    if pkg_file_filter is None:
        pkg_file_filter = pkg_file_filter_from_yaml(DEFAULT_CONFIG_PATH)

    packages = repodata["packages"]
    for pkg_key, pkg_meta in packages.items():

        # for each pkg we need to make sure env prefix is empty
        if env_prefix.is_dir():
            shutil.rmtree(env_prefix)

        env_prefix.mkdir(parents=True, exist_ok=True)

        # create the env at a temp dir
        with tempfile.TemporaryDirectory() as temp_dir:

            # install environment to temp dir
            env_name = "env"
            temp_env_dir = Path(temp_dir) / env_name
            pkg_spec = f"{pkg_meta['name']}={pkg_meta['version']}={pkg_meta['build']}"
            create_env(
                pkg_spec, temp_env_dir, platform="emscripten-32", channels=channels
            )

            js_files = []
            for pkg_meta in iterate_env_pkg_meta(temp_env_dir):

                pkg_outname = pkg_meta["fn"][:-8]
                pkg_name = pkg_meta["name"]

                matchers = pkg_file_filter.get_matchers(pkg_name=pkg_name)

                with tempfile.TemporaryDirectory() as temp_root_dir:

                    temp_dirs = []
                    target_dirs = []
                    for i in range(len(matchers)):
                        temp_dir = os.path.join(temp_root_dir, f"{i}")
                        target_dir = os.path.join(temp_dir, env_name)
                        os.makedirs(target_dir)
                        temp_dirs.append(temp_dir)
                        target_dirs.append(target_dir)

                    has_any_files = split_filter_pkg(
                        env_prefix=temp_env_dir,
                        pkg_meta=pkg_meta,
                        target_dirs=target_dirs,
                        matchers=matchers,
                    )

                    js_files = []
                    for i in range(len(matchers)):
                        if has_any_files[i]:

                            pkg_base_name = f"{pkg_outname}.{i}"

                            emscripten_file_packager(
                                outname=f"{pkg_base_name}",
                                to_mount=env_name,
                                mount_path=env_prefix,
                                export_name=export_name,
                                use_preload_plugins=True,
                                no_node=export_name.startswith("globalThis"),
                                lz4=True,
                                cwd=str(temp_dirs[i]),
                                emsdk_version=emsdk_version,
                            )
                            js_files.append(f"{pkg_base_name}.js")
                            shutil.copy(
                                os.path.join(
                                    str(temp_dirs[i]), f"{pkg_base_name}.data"
                                ),
                                pack_outdir,
                            )
                            shutil.copy(
                                os.path.join(str(temp_dirs[i]), f"{pkg_base_name}.js"),
                                pack_outdir,
                            )

                            extend_js(os.path.join(pack_outdir, f"{pkg_base_name}.js"))

                            js_files.append(f"{pkg_base_name}.js")

                    with open(
                        os.path.join(pack_outdir, f"{pkg_outname}.json"), "w"
                    ) as f:
                        json.dump(js_files, f)


def pack_environment(
    env_prefix: Path,
    outname: str,
    export_name: str,
    pkg_file_filter: Union[PkgFileFilter, None] = None,
    pack_outdir: Union[str, None] = None,
    emsdk_version: Union[str, None] = None,
):
    # name of the env
    env_name = PurePath(env_prefix).parts[-1]

    if pkg_file_filter is None:
        pkg_file_filter = pkg_file_filter_from_yaml(DEFAULT_CONFIG_PATH)

    # create a temp dir and store the filter&copy
    # the data to the tmp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = os.path.join(temp_dir, env_name)
        os.makedirs(target_dir)

        filter_env(
            env_prefix=env_prefix,
            target_dir=target_dir,
            pkg_file_filter=pkg_file_filter,
        )

        emscripten_file_packager(
            outname=outname,
            to_mount=env_name,
            mount_path=env_prefix,
            export_name=export_name,
            use_preload_plugins=True,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=str(temp_dir),
            emsdk_version=emsdk_version,
        )

        if pack_outdir is None:
            pack_outdir = os.getcwd()

        shutil.copy(os.path.join(str(temp_dir), f"{outname}.data"), pack_outdir)
        shutil.copy(os.path.join(str(temp_dir), f"{outname}.js"), pack_outdir)

        extend_js(os.path.join(pack_outdir, f"{outname}.js"))


def pack_file(
    file: Path,
    mount_path: str,
    outname: str,
    export_name: str,
    use_preload_plugins: bool = True,
    silent: bool = False,
):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        os.makedirs(os.path.join(temp_dir_str, "assets"), exist_ok=False)
        shutil.copy2(str(file), os.path.join(temp_dir_str, "assets"))

        emscripten_file_packager(
            outname=outname,
            to_mount="assets/",
            mount_path=mount_path,
            export_name=export_name,
            use_preload_plugins=use_preload_plugins,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=temp_dir_str,
            silent=silent,
        )

        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), os.getcwd())
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), os.getcwd())


def pack_directory(
    directory: Path,
    mount_path: str,
    outname: str,
    export_name: str,
    use_preload_plugins: bool = True,
    silent: bool = False,
):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        os.makedirs(os.path.join(temp_dir_str, "assets"), exist_ok=False)
        assets_dir = os.path.join(temp_dir_str, "assets")
        shutil.copytree(directory, assets_dir, dirs_exist_ok=True)

        emscripten_file_packager(
            outname=outname,
            to_mount="assets/",
            mount_path=mount_path,
            export_name=export_name,
            use_preload_plugins=use_preload_plugins,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=temp_dir_str,
            silent=silent,
        )

        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), os.getcwd())
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), os.getcwd())


def create_env(pkg_name: str, prefix: str, platform: str, channels=None):

    channel_args = ""
    if channels is not None:
        channel_args = " ".join([f" -c {c} " for c in channels])

    cmd = [
        f"$MAMBA_EXE create --yes --prefix {prefix} {channel_args} --platform={platform} --no-deps {pkg_name} "
    ]
    ret = subprocess.run(cmd, shell=True, check=False, capture_output=True)
    if ret.returncode != 0:
        print(ret)
    returncode = ret.returncode
    assert returncode == 0


def pack_conda_pkg(recipe, pack_prefix, pack_outdir, outname, pkg_file_filter):
    """pack a conda pkg with emscriptens filepackager

    Args:
        recipe (dict): the rendered recipe as dict
        pack_prefix (str): path where the packed env will be created
                           (WARNING this will override the envs content)
        pack_outdir (str): destination folder for the created pkgs
    """
    pkg_name = recipe["package"]["name"]
    create_env(pkg_name, pack_prefix, platform="emscripten-32")

    pack_environment(
        env_prefix=pack_prefix,
        outname=outname,
        export_name="globalThis.Module",
        pkg_file_filter=pkg_file_filter,
        pack_outdir=pack_outdir,
    )
