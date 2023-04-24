import subprocess


def create_environment(
    prefix,
    channels=None,
    packages=None,
    platform=None,
    no_deps=False,
    relocate_prefix=None,
    dry_run=False,
    micromamba_exe=None,
    supress_stdout=True,
):
    """Creates a new environment using Micromamba.

    Parameters
    ----------
    prefix (str): The path to the prefix directory in which to create the environment. Defaults to None.
    channels (list[str], optional): A list of additional channels to use when searching for packages. Defaults to None.
    packages (list[str], optional): A list of packages to install in the new environment. Defaults to None.
    platform (str, optional): The platform for which to create the environment (e.g. linux-64, osx-64, win-64). Defaults to None.
    no_deps (bool, optional): Whether to skip the installation of package dependencies. Defaults to False.
    dry_run (bool, optional): Whether to perform a dry run (i.e. print the Micromamba command that would be run) without actually running the command. Defaults to False.
    micromamba_exe (str, optional): The path to the micromamba executable. Defaults to "micromamba".
    supress_stdout (bool, optional): Whether to supress the output of the Micromamba command. Defaults to True.


    Returns
    -------
    None
    """
    if micromamba_exe is None:
        micromamba_exe = "micromamba"
    micromamba_command = [str(micromamba_exe), "create", "-y"]

    if prefix:
        micromamba_command += ["-p", str(prefix)]

    if relocate_prefix:
        micromamba_command += ["--relocate-prefix", str(relocate_prefix)]

    if platform:
        micromamba_command += ["--platform", platform]

    if no_deps:
        micromamba_command += ["--no-deps"]

    if channels:
        for channel in channels:
            micromamba_command += ["-c", str(channel)]

    if packages:
        micromamba_command += packages

    if dry_run:
        print("Dry run: Micromamba command that would be run:")
        print(" ".join(micromamba_command))
        return

    try:
        extra_kwargs = {}
        if supress_stdout:
            extra_kwargs["stdout"] = subprocess.DEVNULL
        subprocess.run(micromamba_command, check=True, **extra_kwargs)  # noqa:  #  noqa: S603
    except subprocess.CalledProcessError as e:
        error_message = f"Error: Micromamba command failed with return code {e.returncode}"
        raise Exception(error_message) from e
