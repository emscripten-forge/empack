import subprocess
import os
import sys
import importlib
from pathlib import Path
import requests
import shutil
import tempfile
import typer
from urllib import request
import json
from pathlib import PurePath
import warnings
from .filter_env import filter_env

EMSDK_VER = "latest"

HERE = Path(__file__).parent


def shrink_conda_meta(prefix):
    conda_meta = os.path.join(prefix, "conda-meta")

    for filename in os.listdir(conda_meta):
        f = os.path.join(conda_meta, filename)
        if os.path.isfile(f) and f.endswith(".json"):
            with open(f, "r") as file:
                data = json.load(file)

                data.pop("paths_data", None)
                data.pop("files", None)

            with open(f, "w") as outfile:
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
            f"FILE_PACKAGER needs to be an env variable pointing to emscpriptens file_packager.py"
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
        file_packager_path,
        f"{outname}.data",
        f"--preload",
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
    if not silent:
        subprocess.run(cmd, shell=False, check=True, cwd=cwd)
    else:
        subprocess.run(
            cmd,
            shell=False,
            check=True,
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )


def pack_environment(
    env_prefix: Path, outname, export_name, pack_outdir=None, download_emsdk=None
):
    # name of the env
    env_name = PurePath(env_prefix).parts[-1]
    env_root = os.path.join(*PurePath(env_prefix).parts[:-1])


    # create a temp dir and store the filter&copy
    # the data to the tmp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        target_dir = os.path.join(temp_dir, env_name)
        os.makedirs(target_dir)

        filter_env(env_prefix=env_prefix, target_dir=target_dir)

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


def pack_python_core(env_prefix: Path, outname, version, export_name, download_emsdk):
    warnings.warn(
        "pack_python_core is deprecated, use `pack_environment`",
        DeprecationWarning,
    )
    pack_environment(
        env_prefix=env_prefix,
        outname=outname,
        export_name=export_name,
        download_emsdk=download_emsdk,
    )


def pack_file(
    file: Path,
    mount_path,
    outname: str,
    export_name,
    use_preload_plugins=True,
    silent=False,
):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        os.makedirs(os.path.join(temp_dir_str, "assets"), exist_ok=False)
        shutil.copy2(str(file), os.path.join(temp_dir_str, "assets"))

        emscripten_file_packager(
            outname=outname,
            to_mount=f"assets/",
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


def create_env(pkg_name, prefix, platform):
    # cmd = ['$MAMBA_EXE' ,'create','--prefix', prefix,'--platform=emscripten-32'] + [pkg_name] #+ ['--dryrun']
    cmd = [
        f"$MAMBA_EXE create --yes --prefix {prefix} --platform={platform} --no-deps {pkg_name}"
    ]
    ret = subprocess.run(cmd, shell=True, check=False, capture_output=True)
    if ret.returncode != 0:
        print(ret)
    returncode = ret.returncode
    assert returncode == 0


def make_pkg_name(recipe):

    name = recipe["package"]["name"]
    version = recipe["package"]["version"].replace(".", "_")
    build_number = recipe["build"].get("number", 0)

    return f"{name}_v_{version}__bn_{build_number}"


def pack_conda_pkg(recipe, pack_prefix, pack_outdir, outname):
    """pack a conda pkg with emscriptens filepackager

    Args:
        recipe (dict): the rendered recipe as dict
        pack_prefix (str): path where the packed env will be created (WARNING this will override the envs content)
        pack_outdir (str): destination folder for the created pkgs
    """
    pkg_name = recipe["package"]["name"]
    print("pack_prefix", pack_prefix)
    create_env(pkg_name, pack_prefix, platform="emscripten-32")
    # shrink_conda_meta(pack_prefix)

    pack_environment(
        env_prefix=pack_prefix,
        outname=outname,
        export_name="globalThis.Module",
        pack_outdir=pack_outdir,
    )
