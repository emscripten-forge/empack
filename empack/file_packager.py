import subprocess
import os
import sys
from pathlib import Path
import shutil
import tempfile
import typer
import json

EMSDK_VER = "latest"


def shrink_conda_meta(prefix):
    conda_meta = os.path.join(prefix,'conda-meta')

    for filename in os.listdir(conda_meta):
        f = os.path.join(conda_meta, filename)
        if os.path.isfile(f) and f.endswith(".json"):
            with open(f, "r") as file:
                data = json.load(file)

                data.pop('paths_data',None)
                data.pop('files',None)

            with open(f, 'w') as outfile:
                json.dump(data, outfile)


def make_ignore_patterns(prefix):
    return shutil.ignore_patterns(
        "*.pyx",
        "*.pyc",
        "*.pck",
        "*.o",
        "*.saa",
        "Makefile",
        "*.wasm",
        "*cpython-310.data",
        "*cpython-311.data",
        "*.a",
        "*.zip",
        "*.tar.gz",
        "*.tar",
        "__pycache__/**",
        "test_*.py",
        ".js",
        ".ts",
        ".c",
        ".h",
        ".cpp",
        ".hpp"
        ".cxx",
        ".hxx",
        "RECORD",
        os.path.join(prefix, "bin", "*"),
        os.path.join(prefix, "bin"),
        os.path.join(prefix, "include", "*"),
        os.path.join(prefix, "include"),
        os.path.join(prefix, "lib", "pkgconfig", "*"),
        os.path.join(prefix, "lib", "pkgconfig"),
        os.path.join(prefix, "lib", "python3.10","test/**"),
        os.path.join(prefix, "lib", "python3.10","tkinter"),
        os.path.join(prefix, "lib", "python3.10","pydoc_data"),
        os.path.join(prefix, "lib", "python3.10","pydoc.py"),
        os.path.join(prefix, "lib/python3.10/site-packages/bokeh/server/static"),
        os.path.join(prefix, "lib/python3.10/site-packages/pandas/_libs/"),
        os.path.join(prefix, "lib/python3.10/site-packages/astropy/extern/jquery/")
    )


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(
                s, d, symlinks, ignore=ignore, ignore_dangling_symlinks=True
            )
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
            emsdk_dir
            / "upstream"
            / "emscripten"
            / "tools"
            / "file_packager.py"
        )

        # If emsdk is not initialized, we do it
        if not os.path.isfile(conda_file_packager):
            subprocess.run(
                ["emsdk", "install", EMSDK_VER],
                shell=False,
                check=True
            )
            subprocess.run(
                ["emsdk", "activate", EMSDK_VER],
                shell=False,
                check=True
            )
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

    if lz4:
        cmd += ["--lz4"]
    print(cmd)
    subprocess.run(cmd, shell=False, check=True, cwd=cwd)


def pack_python_core(env_prefix: Path, outname, version, export_name):
    ensure_python(env_prefix=env_prefix, version=version)

    lib_dir = env_prefix / "lib"
    python_lib_dir = lib_dir / f"python{version}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        ignore = make_ignore_patterns(env_prefix)
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


def pack_conda_pkg(recipe, pack_prefix, pack_outdir):
    """pack a conda pkg with emscriptens filepackager

    Args:
        recipe (dict): the rendered recipe as dict
        pack_prefix (str): path where the packed env will be created (WARNING this will override the envs content)
        pack_outdir (str): destination folder for the created pkgs
    """
    pkg_name = recipe["package"]["name"]
    print("pack_prefix",pack_prefix)
    create_env(pkg_name, pack_prefix, platform="emscripten-32")
    shrink_conda_meta(pack_prefix)

    pkg_full_name = make_pkg_name(recipe)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_str = str(temp_dir)

        if os.path.isdir(os.path.join(pack_prefix, "bin")):
            shutil.rmtree(os.path.join(pack_prefix, "bin"), ignore_errors=True)

        if os.path.isdir(os.path.join(pack_prefix, "lib", "pkgconfig")):
            shutil.rmtree(
                os.path.join(pack_prefix, "lib", "pkgconfig"), ignore_errors=True
            )

        ignore = make_ignore_patterns(pack_prefix)
        # ignore=None
        print(f"copy tree from  {pack_prefix} to {temp_dir_str}")
        d = os.path.join(temp_dir_str, "the_env")
        copytree(pack_prefix, temp_dir_str, ignore=ignore)

        mount_path = pack_prefix
        export_name = "globalThis.Module"
        outname = pkg_full_name
        emscripten_file_packager(
            outname=outname,
            to_mount=temp_dir_str,
            mount_path=pack_prefix,
            export_name=export_name,
            use_preload_plugins=True,
            no_node=export_name.startswith("globalThis"),
            lz4=True,
            cwd=temp_dir_str,
        )
        if not os.path.isdir(pack_outdir):
            os.path.mkdir(pack_outdir)
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.data"), pack_outdir)
        shutil.copy(os.path.join(temp_dir_str, f"{outname}.js"), pack_outdir)
