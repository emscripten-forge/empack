import os
import subprocess
from pathlib import Path


def save_as_squashfs(
    output_filename,
    filtered_prefix,
    filenames,
    compresslevel=9
):
    if not Path(output_filename).parts[-1].endswith(f".sqshfs"):
        error_message = (
            f"Output filename {output_filename} does not end with .sqshfs"
        )
        raise RuntimeError(error_message)

    try:
        os.chdir(filtered_prefix)
        mksquashfs_command = ['mksquashfs', '-', output_filename, '-cpiostyle0', '-b', '128K', '-comp', 'zstd', '-noappend']
        # print("peak mksq", mksquashfs_command)
        process = subprocess.Popen(
            mksquashfs_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=filtered_prefix
        )
        # Note: we may want to string c++ source files?
        for filename in filenames:
            # print("peakfilename",filtered_prefix,  filename)
            process.stdin.write(str(filename).encode() + b'\0')

        stdout, stderr = process.communicate()
        process.stdin.close()

        if stdout:
            print(f"mksquashfs stdout:\n{stdout.decode()}")
        if stderr:
            print(f"mksquashfs stderr:\n{stderr.decode()}")
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode,
                mksquashfs_command,
                output=stdout,
                stderr=stderr
            )

    except FileNotFoundError:
        print("Error: 'mksquashfs' command not found. Install it with conda install squashfs-tools")
