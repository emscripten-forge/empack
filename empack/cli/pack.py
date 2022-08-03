from pathlib import Path
from typing import Optional

import typer

from empack.file_packager import pack_environment, pack_file
from empack.file_patterns import pkg_file_filter_from_yaml

from .app import app

# packaging
pack_app = typer.Typer()
app.add_typer(pack_app, name="pack")


@pack_app.command()
def file(file: Path, mount_path, outname: str, export_name="globalThis.Module"):

    pack_file(
        file=file, mount_path=mount_path, outname=outname, export_name=export_name
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
        help="base filename of outputs:  {outname}.js / {outname}.data",
    ),
    config: Path = typer.Option(  # noqa: B008
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
):

    # check that the environment prefix existis
    if not env_prefix.is_dir():
        print(f"""empack error: env-prefix `{env_prefix}` directory does not exist""")
        raise typer.Exit(code=1)

    # check that config file exists
    if not config.is_file():
        print(f"""empack error: config file `{config}` file does not exist""")
        raise typer.Exit(code=1)

    # load config
    pkg_file_filter = pkg_file_filter_from_yaml(config)

    # downstream `download_emsdk` handles two things:
    # if the emsdk should be downloaded and the version
    if not download_emsdk:
        download_emsdk = None
    else:
        download_emsdk = emsdk_version

    pack_environment(
        env_prefix=env_prefix,
        outname=outname,
        export_name=export_name,
        download_emsdk=download_emsdk,
        pkg_file_filter=pkg_file_filter,
    )
