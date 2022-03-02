import typer
import textwrap
import inspect
import subprocess
import os
import sys
import pprint
from pathlib import Path
import shutil
import tempfile



def echo(text:str):
    typer.echo(inspect.cleandoc(text))


app = typer.Typer()


@app.command()
def hello(name: str):
    typer.echo(f"Hello {name}")


@app.command()
def pack_python(env_prefix: Path, outname: str = 'python_data', version: str = "3.11"):
    if not env_prefix.is_dir():
        echo(f'{env_prefix} is not a dir')
        raise typer.Exit()

    lib_dir = env_prefix / "lib" 
    python_lib_dir = lib_dir / f"python{version}"
    if not python_lib_dir.is_dir():
        echo(f'{python_lib_dir} is not a dir')
        echo(f"""python{version} could be missing 
             or verion {version} might be wrong""")
        raise typer.Exit()

    file_packager_path = os.environ.get('FILE_PACKAGER')
    if file_packager_path is None:
        echo(f'FILE_PACKAGER needs to be an env variable pointing to emscpriptens file_packager.py')


    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = "/home/derthorsten/mytemp" 
        temp_dir_str = str(temp_dir)

        ignore = shutil.ignore_patterns('*.pyc','*.o','*.so','Makefile')
        ignore=None
        py_temp_dir = os.path.join(temp_dir_str,f"python{version}")
        shutil.copytree(python_lib_dir, py_temp_dir, ignore=ignore)


        print("env_prefix",env_prefix)


        mount_path = os.path.join(env_prefix, f'lib/python{version}')

        cmd = [sys.executable,file_packager_path]
        cmd += [f'{outname}.data',f'--preload', f'python{version}@{mount_path}', f'--js-output={outname}.js']
        cmd += ['--export-name=globalThis.Module']
        # cmd += ['--lz4']
        pprint.pprint(cmd)
        subprocess.run(cmd, shell=False, check=True, cwd=temp_dir_str)

        shutil.rmtree(py_temp_dir)
        shutil.copy(os.path.join(temp_dir_str, f'{outname}.data'),
            os.getcwd()
        )
        shutil.copy(os.path.join(temp_dir_str, f'{outname}.js'),
            os.getcwd()
        )





if __name__ == "__main__":
    app()