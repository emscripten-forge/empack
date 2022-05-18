from .app import app
import typer
from pathlib import Path

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
