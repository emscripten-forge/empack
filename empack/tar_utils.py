import tarfile
from pathlib import Path

ALLOWED_FORMATS = ["gz"]


def save_as_tarfile(
    output_filename,
    filenames,
    arcnames,
    compression_format=ALLOWED_FORMATS[0],
    compresslevel=9,
):
    if compression_format not in ALLOWED_FORMATS:
        error_message = (
            f"Compression format {compression_format} not supported, only {ALLOWED_FORMATS} are"
            " supported."
        )
        raise RuntimeError(error_message)

    if not Path(output_filename).parts[-1].endswith(f".tar.{compression_format}"):
        error_message = (
            f"Output filename {output_filename} does not end with .tar.{compression_format}"
        )
        raise RuntimeError(error_message)

    with tarfile.open(
        output_filename, f"w:{compression_format}", compresslevel=compresslevel
    ) as tar:
        for file, arcname in zip(filenames, arcnames):
            tar.add(file, arcname=arcname)
