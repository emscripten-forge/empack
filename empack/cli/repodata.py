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
    outfile: Path = typer.Option(  # noqa: B008
        ...,
        "--outfile",
        "-o",
        help="location of noarch repodata json",
    ),
    indent: bool = typer.Option(  # noqa: B008
        False,
        "--indent",
        "-s",
        help="if true, we add indent of 4 to the json",
    ),
):

    with open(noarch_repodata, "r") as f_in:
        noarch_repodata = json.load(f_in)

    with open(arch_repodata, "r") as f_in:
        arch_repodata = json.load(f_in)

    shrinked_noarch_repodata = noarch_repodata
    shrinked_noarch_repodata = filter_out_by_pkg_name(shrinked_noarch_repodata)
    # shrinked_noarch_repodata = shrink_pkg_meta_items(shrinked_noarch_repodata)
    shrinked_noarch_repodata = only_keep_latest_build_number(shrinked_noarch_repodata)
    shrinked_noarch_repodata = shrink_trivial_unsatisfiable(
        shrinked_noarch_repodata, arch_repodata
    )
    shrinked_noarch_repodata = filter_out_explict_unsat_deps(shrinked_noarch_repodata)
    shrinked_noarch_repodata = filter_out_by_micromamba(shrinked_noarch_repodata)
    with open(outfile, "w") as f_out:
        extra_kwargs = {}
        if indent:
            extra_kwargs["indent"] = 4
        repodata = json.dump(shrinked_noarch_repodata, f_out, **extra_kwargs)
