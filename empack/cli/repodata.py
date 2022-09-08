import os
from pathlib import Path
from typing import List, Optional

import typer

from ..shrink_repodata import *

from .app import app
from .err import exit_with_err

# packaging
repodata_app = typer.Typer()
app.add_typer(repodata_app, name="repodata")


# https://repo.mamba.pm/emscripten-forge/emscripten-32/repodata.json
# https://repo.mamba.pm/conda-forge/noarch/repodata.json
@repodata_app.command()
def shrink(
    noarch_repodata: Path = typer.Option(  # noqa: B008
        ...,
        "--noarch-repodata",
        "-n",
        help="location of noarch repodata json",
    ),
    arch_repodata: Path = typer.Option(  # noqa: B008
        ...,
        "--arch-repodata",
        "-a",
        help="location of arch repodata json",
    ),
    split: bool = typer.Option(  # noqa: B008
        False,
        "--split",
        "-s",
        help="if true, each pkg is packaged in its on *.js/*data",
    ),
):

    pass
