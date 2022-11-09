import os
from pathlib import Path
from typing import List, Optional
import json
import typer

from ..repodata import download_and_shrink_repodata

from .app import app
from .err import exit_with_err

# packaging
repodata_app = typer.Typer()
app.add_typer(repodata_app, name="repodata")


@repodata_app.command()
def shrink(
    arch: str = typer.Option(  # noqa: B008
        "https://beta.mamba.pm/get/emscripten-forge/emscripten-32/repodata.json.bz2"
        "--arch",
        "-a",
        help="arch / emscripten-32 repodata",
    ),
    no_arch: str = typer.Option(  # noqa: B008
        "https://beta.mamba.pm/get/conda-forge/noarch/repodata.json.bz2",
        "--no-arch",
        "-n",
        help="no-arch repodata",
    ),
    outdir: Path = typer.Option(  # noqa: B008
        None,
        "--outdir",
        "-o",
        help="outdir",
    ),
):
    repodata_urls = {"arch": arch, "noarch": no_arch}

    download_and_shrink_repodata(repodata_urls, outdir=outdir)
