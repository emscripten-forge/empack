import typer

from ..version import __version__
from .app import app


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(  # noqa: B008
        None, "--version", "-v", callback=version_callback
    ),
):
    pass
