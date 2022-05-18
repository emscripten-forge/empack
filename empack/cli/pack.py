from .app import app
import typer
from pathlib import Path
from typing import List, Optional


from empack.file_packager import (
    pack_file,
    pack_python_core,
)


# packaging
pack_app = typer.Typer()
app.add_typer(pack_app, name="pack")


@pack_app.command()
def file(file: Path, mount_path, outname: str, export_name="globalThis.Module"):

    pack_file(
        file=file, mount_path=mount_path, outname=outname, export_name=export_name
    )


# @pack_app.command()
# def conda_pkg(
#     pkg_name,
#     prefix,
#     env_name,
#     channels: Optional[List[str]] = typer.Option(
#         ["https://repo.mamba.pm/emscripten-forge", "conda-forge"]
#     ),
#     target_platform: Optional[str] = typer.Option("emscripten-32"),
#     override: Optional[bool] = typer.Option(False),
# ):
#     print(f"{override=}")
#     pack_conda_pkg(
#         pkg_name=pkg_name,
#         channels=channels,
#         prefix=prefix,
#         override=override,
#         target_platform=target_platform,
#     )


# emscripten
pack_python_app = typer.Typer()
pack_app.add_typer(pack_python_app, name="python")


@pack_python_app.command()
def core(
    env_prefix: Path,
    outname: str = "python_data",
    version: str = "3.11",
    export_name="globalThis.Module",
):
    pack_python_core(
        env_prefix=env_prefix,
        outname=outname,
        version=version,
        export_name=export_name,
    )
