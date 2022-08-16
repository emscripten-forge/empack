import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath
from typing import Union
from urllib import request

import requests
import typer

from .extend_js import extend_js
from .file_patterns import PkgFileFilter
from .filter_env import filter_env, filter_pkg, iterate_env_pkg_meta

EMSDK_VER = "latest"

HERE = Path(__file__).parent


def shrink_conda_meta(prefix, target_dir=None):
    if not target_dir:
        target_dir = Path(prefix)

    prefix = Path(prefix)

    conda_meta = prefix / "conda-meta"
    target_dir = Path(target_dir) / "conda-meta"
    target_dir.mkdir(parents=True, exist_ok=True)

    for p in conda_meta.glob("*.json"):
        with open(p, "r") as file:
            data = json.load(file)

            data.pop("paths_data", None)
            data.pop("files", None)

        with open(target_dir / p.name, "w") as outfile:
            json.dump(data, outfile)


def download_and_setup_emsdk(emsdk_version):
    tag = None
    if emsdk_version == "latest":
        tags = requests.get("https://api.github.com/repos/emscripten-core/emsdk/tags")
        if tags.content:
            tag = json.loads(tags.content)[0]["name"]
    else:
        tag = emsdk_version

    emsdk_dir = f"emsdk-{tag}"
    file_packager_path = (
        HERE / emsdk_dir / "upstream" / "emscripten" / "tools" / "file_packager.py"
    )

    if not os.path.isdir(HERE / emsdk_dir):
        file = f"{tag}.zip"
        request.urlretrieve(
            f"https://github.com/emscripten-core/emsdk/archive/refs/tags/{file}",
            HERE / file,
        )
        shutil.unpack_archive(HERE / file, HERE)
        os.rename(HERE / f"emsdk-{tag}", HERE / emsdk_dir)
        os.remove(HERE / file)

        subprocess.run(
            [sys.executable, str(HERE / emsdk_dir / "emsdk.py"), "install", tag],
            shell=False,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(HERE / emsdk_dir / "emsdk.py"), "activate", tag],
            shell=False,
            check=True,
        )

    assert os.path.exists(file_packager_path)

    return file_packager_path


def get_file_packager_path():
    # First check for the emsdk conda package
    emsdk_dir = None
    try:
        import emsdk

        emsdk_dir = Path(emsdk.__file__).parent
    except ImportError:
        pass

    if emsdk_dir is not None:
        # emsdk was installed with conda
        conda_file_packager = (
            emsdk_dir / "upstream" / "emscripten" / "tools" / "file_packager.py"
        )

        # If emsdk is not initialized, we do it
        if not os.path.isfile(conda_file_packager):
            subprocess.run(["emsdk", "install", EMSDK_VER], shell=False, check=True)
            subprocess.run(["emsdk", "activate", EMSDK_VER], shell=False, check=True)
            os.environ["EMSDK"] = str(emsdk_dir)
            os.environ["EM_CONFIG"] = str(Path(emsdk_dir) / ".emscripten")

        assert os.path.isfile(conda_file_packager)

        return conda_file_packager

    # Then check for the environment variable
    file_packager_path = os.environ.get("FILE_PACKAGER")
    if file_packager_path is None:
        print(
            "FILE_PACKAGER needs to be an env variable pointing to emscpriptens file_packager.py"
        )
        raise typer.Exit()
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
    download_emsdk=None,
):
    if download_emsdk:
        file_packager_path = download_and_setup_emsdk(download_emsdk)
    else:
        file_packager_path = get_file_packager_path()

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
    pkg_file_filter: PkgFileFilter,
    pack_outdir: Union[str, None] = None,
    download_emsdk: Union[str, None] = None,
):
    if pack_outdir is None:
        pack_outdir = os.getcwd()

    # name of the env
    env_name = PurePath(env_prefix).parts[-1]
    print(env_name)

    all_pks = []
    for pkg_meta in iterate_env_pkg_meta(env_prefix):

        pkg_outname = pkg_meta["fn"][:-8]

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = os.path.join(temp_dir, env_name)
            os.makedirs(target_dir)

        has_any_file = filter_pkg(
            env_prefix=env_prefix,
            pkg_meta=pkg_meta,
            target_dir=target_dir,
            pkg_file_filter=pkg_file_filter,
        )
        if has_any_file:
            all_pks.append(pkg_outname)
            emscripten_file_packager(
                outname=pkg_outname,
                to_mount=env_name,
                mount_path=env_prefix,
                export_name=export_name,
                use_preload_plugins=True,
                no_node=export_name.startswith("globalThis"),
                lz4=True,
                cwd=str(temp_dir),
                download_emsdk=download_emsdk,
            )

            shutil.copy(os.path.join(str(temp_dir), f"{pkg_outname}.data"), pack_outdir)
            shutil.copy(os.path.join(str(temp_dir), f"{pkg_outname}.js"), pack_outdir)

            extend_js(os.path.join(pack_outdir, f"{pkg_outname}.js"))

    # create the base js file
    lines = []
    for pkg_outname in all_pks:
        lines.append(f"    promises.push(import('./{pkg_outname}.js'));")
    txt = "\n".join(lines)
    js_import_all_func = f"""export default async function(){{
    let promises = [];
{txt}
    await Promise.all(promises);
}}
    """
    with open(os.path.join(pack_outdir, f"{outname}.js"), "w") as f:
        f.write(js_import_all_func)


def pack_environment(
    env_prefix: Path,
    outname: str,
    export_name: str,
    pkg_file_filter: PkgFileFilter,
    pack_outdir: Union[str, None] = None,
    download_emsdk: Union[str, None] = None,
):
    # name of the env
    env_name = PurePath(env_prefix).parts[-1]

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
        shrink_conda_meta(env_prefix, target_dir=target_dir)

        emscripten_file_packager(
            outname=outname,
            to_mount=env_name,
            mount_path=env_prefix,
            export_name=export_name,
            use_preload_plugins=True,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=str(temp_dir),
            download_emsdk=download_emsdk,
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


def create_env(pkg_name: str, prefix: str, platform: str):
    cmd = [
        f"$MAMBA_EXE create --yes --prefix {prefix} --platform={platform} --no-deps {pkg_name}"
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
