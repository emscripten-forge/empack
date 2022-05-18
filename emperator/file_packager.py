import subprocess
import os
import sys
from pathlib import Path
import shutil
import tempfile
import typer
import glob
import json


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def ensure_python(env_prefix: Path, version: str):
    if not env_prefix.is_dir():
        print(f"{env_prefix} is not a dir")
        raise typer.Exit()
    lib_dir = env_prefix / "lib"
    python_lib_dir = lib_dir / f"python{version}"
    if not python_lib_dir.is_dir():

        raise RuntimeError(
            f""" {python_lib_dir} is not a dir"
                python{version} could be missing
                 or verion {version} might be wrong"""
        )


def get_file_packager_path():
    # First check for the conda prefix
    current_conda_env = os.environ.get("CONDA_PREFIX")
    if current_conda_env is not None:
        conda_file_packager = (
            Path(current_conda_env)
            / "opt"
            / "emsdk"
            / "upstream"
            / "emscripten"
            / "tools"
            / "file_packager.py"
        )
        if os.path.isfile(conda_file_packager):
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
):
    print("outname", outname)
    cmd = [
        sys.executable,
        get_file_packager_path(),
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
    print(cmd)
    subprocess.run(cmd, shell=False, check=True, cwd=cwd)


def pack_python_core(env_prefix: Path, outname, version, export_name):
    ensure_python(env_prefix=env_prefix, version=version)

    lib_dir = env_prefix / "lib"
    python_lib_dir = lib_dir / f"python{version}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        ignore = shutil.ignore_patterns(
            "*.pyc", "*.o", "*.saa", "Makefile", "*.wasm", "*cpython-311.data", "*.a"
        )
        # ignore=None
        py_temp_dir = os.path.join(temp_dir_str, f"python{version}")
        shutil.copytree(python_lib_dir, py_temp_dir, ignore=ignore)

        mount_path = os.path.join(env_prefix, f"lib/python{version}")

        emscripten_file_packager(
            outname=outname,
            to_mount=f"python{version}",
            mount_path=mount_path,
            export_name=export_name,
            use_preload_plugins=True,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=temp_dir_str,
        )

        shutil.rmtree(py_temp_dir)
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), os.getcwd())
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), os.getcwd())


def pack_file(
    file: Path, mount_path, outname: str, export_name, use_preload_plugins=True
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
        )

        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), os.getcwd())
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), os.getcwd())


def create_env(pkg_name, prefix, platform):
    # cmd = ['$MAMBA_EXE' ,'create','--prefix', prefix,'--platform=emscripten-32'] + [pkg_name] #+ ['--dryrun']
    cmd = [
        f"$MAMBA_EXE install --yes --prefix {prefix} --platform={platform} --no-deps {pkg_name}"
    ]
    ret = subprocess.run(cmd, shell=True)
    returncode = ret.returncode
    assert returncode == 0


def get_pkg_info(pkg_name, prefix):

    # load *.json from prefix/conda-meta
    meta_path = os.path.join(prefix, "conda-meta", "*.json")
    pkg_jsons = glob.glob(meta_path)
    print(pkg_jsons)
    assert len(pkg_jsons) == 1
    pkg_json = pkg_jsons[0]

    with open(pkg_json) as json_file:
        data = json.load(json_file)
        # print(data)
    path = data["package_tarball_full_path"]
    head, tail = os.path.split(path)
    return tail[: -len(".tar.bz2")]


def pack_conda_pkg(
    recipe,
    pkg_name,
    channels,
    prefix,
    target_platform,
    override=False,
    filter=None,
):

    # create the env which only contains the pkg but not
    # the dependencies
    create_env(pkg_name, prefix, platform=target_platform)

    pkg_full_name = get_pkg_info(pkg_name, prefix)
    print(pkg_full_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        ignore = shutil.ignore_patterns(
            "*.pyc",
            "*.o",
            "*.saa",
            "Makefile",
            "*.wasm",
            "*cpython-311.data",
            "*.a",
            "*.zip",
            "*.tar.gz",
        )
        # ignore=None
        print(f"copy tree from  {prefix} to {temp_dir_str}")
        d = os.path.join(temp_dir_str, "the_env")
        copytree(prefix, temp_dir_str, ignore=ignore)

        mount_path = prefix
        export_name = "globalThis.Module"
        outname = pkg_full_name
        emscripten_file_packager(
            outname=outname,
            to_mount=prefix,
            mount_path=prefix,
            export_name=export_name,
            use_preload_plugins=True,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=temp_dir_str,
        )

        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), os.getcwd())
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), os.getcwd())
