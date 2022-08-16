import typer


def exit_with_err(msg, code=1):
    print(msg)
    raise typer.Exit(code=code)
