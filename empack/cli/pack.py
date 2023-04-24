from pathlib import Path
from typing import Optional

import typer

from empack.file_patterns import pkg_file_filter_from_yaml
from empack.pack import DEFAULT_CONFIG_PATH, pack_env

from .app import app

# packaging
pack_app = typer.Typer()
app.add_typer(pack_app, name="pack")


@pack_app.command(
    name="env",
    help="""Pack an environment into a multiple tarballs:
This will pack and exisiting enviroment into multiple tarballs
and a json file with a list of package filenmmes.
""",
)
def pack_env_cli(
    env_prefix: str = typer.Option(  # noqa: B008
        ...,
        "--env-prefix",
        "-e",
        help="path of the env in host filesystem",
    ),
    relocate_prefix: str = typer.Option(  # noqa: B008
        "/",
        "--relocate-prefix",
        "-r",
        help="path of the env in the the virtual filesystem",
    ),
    config: list[Path] = typer.Option(  # noqa: B008
        [DEFAULT_CONFIG_PATH],
        "--config",
        "-c",
        help="path to a .yaml file with the empack config",
    ),
    use_cache: Optional[bool] = typer.Option(  # noqa: B008
        True,
        "--use-cache/--no-use-cache",
        help="use caching",
    ),
    cache_dir: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--cache-dir",
        help="cache directory",
    ),
    outdir: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--outdir",
        "-o",
        help="if no output directory is specified the current workdir is used",
    ),
    compresslevel: Optional[int] = typer.Option(  # noqa: B008
        9, "--compresslevel", "-l", help="compression level"
    ),
):
    file_filters = pkg_file_filter_from_yaml(*config)

    pack_env(
        env_prefix=env_prefix,
        relocate_prefix=relocate_prefix,
        file_filters=file_filters,
        outdir=outdir,
        cache_dir=cache_dir,
        use_cache=use_cache,
        compresslevel=compresslevel,
    )
