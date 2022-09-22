import os
from pathlib import Path
from typing import List, Optional
import json
import typer

from ..file_packager import (
    pack_environment,
    pack_file,
    pack_repodata,
    split_pack_environment,
)
from ..file_patterns import pkg_file_filter_from_yaml
from ..inspect import inspect_packed

from .app import app
from .err import exit_with_err

# packaging
pack_app = typer.Typer()
app.add_typer(pack_app, name="pack")


@pack_app.command()
def file(file: Path, mount_path, outname: str, export_name="globalThis.Module"):

    pack_file(
        file=file, mount_path=mount_path, outname=outname, export_name=export_name
    )


@pack_app.command()
def directory(
    directory: Path, mount_path, outname: str, export_name="globalThis.Module"
):

    pack_directory(
        directory=directory,
        mount_path=mount_path,
        outname=outname,
        export_name=export_name,
    )


@pack_app.command()
def env(
    env_prefix: Path = typer.Option(  # noqa: B008
        ...,
        "--env-prefix",
        "-e",
        help="location/prefix of the emscripten-32 environment",
    ),
    outname: str = typer.Option(  # noqa: B008
        ...,
        "--outname",
        "-o",
        help="""base filename of outputs:  {outname}.js / {outname}.data""",
    ),
    outdir: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--outdir",
        "-t",
        help="if no output directory is specified the current workdir is used",
    ),
    config: List[Path] = typer.Option(  # noqa: B008
        ..., "--config", "-c", help="path to a .yaml file with the empack config"
    ),
    export_name: str = typer.Option(  # noqa: B008
        "globalThis.Module", "--export-name", "-n"
    ),  # noqa: B008
    download_emsdk: bool = typer.Option(  # noqa: B008
        False, "--download-emsdk", "-d", help="should emsdk be downloaded"
    ),
    emsdk_version: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--emsdk-version",
        "-v",
        help="emsdk version (only useful when --download-emsdk is used)",
    ),
    split: bool = typer.Option(  # noqa: B008
        False,
        "--split",
        "-s",
        help="if true, each pkg is packaged in its on *.js/*data",
    ),
):
    # check that the environment prefix existis
    if not env_prefix.is_dir():
        exit_with_err(
            f"""empack error: env-prefix `{env_prefix}` directory does not exist"""
        )

    # check that at least one config file exists
    if len(config) < 0:
        exit_with_err("""empack error: at least one config file must be provided""")

    for i, p in enumerate(config):
        if not p.is_file():
            exit_with_err(
                f"""empack error: config file #{i} `{p}` file does not exist"""
            )

    if outdir is not None:
        if not os.path.exists(outdir):
            os.makedirs(outdir)

    # load config
    pkg_file_filter = pkg_file_filter_from_yaml(*config)

    # downstream `download_emsdk` handles two things:
    # if the emsdk should be downloaded and the version
    if not download_emsdk:
        download_emsdk = None
    else:
        download_emsdk = emsdk_version

    if not split:
        pack_environment(
            env_prefix=env_prefix,
            outname=outname,
            export_name=export_name,
            download_emsdk=download_emsdk,
            pkg_file_filter=pkg_file_filter,
            pack_outdir=outdir,
        )
    else:
        split_pack_environment(
            env_prefix=env_prefix,
            outname=outname,
            export_name=export_name,
            download_emsdk=download_emsdk,
            pkg_file_filter=pkg_file_filter,
            pack_outdir=outdir,
        )


@pack_app.command()
def repodata(
    repodata: Path = typer.Option(  # noqa: B008
        ...,
        "--repodata",
        "-r",
        help="location/prefix of the emscripten-32 environment",
    ),
    env_prefix: Path = typer.Option(  # noqa: B008
        ...,
        "--env-prefix",
        "-e",
        help="""location/prefix where the files are bundled. 
                This path is also where files are mounted in emscriptens virtual file systen
            """,
    ),
    config: List[Path] = typer.Option(  # noqa: B008
        ..., "--config", "-c", help="path to a .yaml file with the empack config"
    ),
    channel: List[str] = typer.Option(  # noqa: B008
        None, "--channel", "-s", help="channels to use"
    ),
    outdir: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--outdir",
        "-t",
        help="if no output directory is specified the current workdir is used",
    ),
    export_name: str = typer.Option(  # noqa: B008
        "globalThis.Module", "--export-name", "-n"
    ),  # noqa: B008
    download_emsdk: bool = typer.Option(  # noqa: B008
        False, "--download-emsdk", "-d", help="should emsdk be downloaded"
    ),
    emsdk_version: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--emsdk-version",
        "-v",
        help="emsdk version (only useful when --download-emsdk is used)",
    ),
):

    # check that the environment prefix existis
    if not repodata.is_file():
        exit_with_err(f"""empack error: repodata `{repodata}` file does not exist""")
    with open(repodata, "r") as f:
        repodata = json.load(f)

    # check that at least one config file exists
    if len(config) < 0:
        exit_with_err("""empack error: at least one config file must be provided""")

    for i, p in enumerate(config):
        if not p.is_file():
            exit_with_err(
                f"""empack error: config file #{i} `{p}` file does not exist"""
            )

    if outdir is not None:
        if not os.path.exists(outdir):
            os.makedirs(outdir)

    # load config
    pkg_file_filter = pkg_file_filter_from_yaml(*config)

    # downstream `download_emsdk` handles two things:
    # if the emsdk should be downloaded and the version
    if not download_emsdk:
        download_emsdk = None
    else:
        download_emsdk = emsdk_version

    pack_repodata(
        repodata=repodata,
        env_prefix=env_prefix,
        channels=channel,
        export_name=export_name,
        download_emsdk=download_emsdk,
        pkg_file_filter=pkg_file_filter,
        pack_outdir=outdir,
    )


@pack_app.command()
def inspect(
    js_file: Path = typer.Option(  # noqa: B008
        ...,
        "--js-file",
        "-j",
        help="location of the javascript file (generated by empack)",
    )
):

    inspect_packed(js_file)
