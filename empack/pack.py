from .micromamba_wrapper import create_environment
from .filter_env import filter_pkg, filter_env, iterate_env_pkg_meta
from tempfile import TemporaryDirectory
from pathlib import Path, PosixPath
import os.path
import json
import shutil
from appdirs import user_cache_dir
import sys
import os
from .tar_utils import save_as_tarfile, ALLOWED_FORMATS


EMPACK_CACHE_DIR = Path(user_cache_dir("empack"))
PACKED_PACKAGES_CACHE_DIR = EMPACK_CACHE_DIR / "packed_packages_cache"
PACKED_PACKAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_CONFIG_PATH = Path(sys.prefix) / "share" / "empack" / "empack_config.yaml"


def filename_base_from_meta(pkg_meta):
    name = pkg_meta["name"]
    version = pkg_meta["version"]
    build = pkg_meta["build"]
    pkg_string = f"{name}-{version}-{build}"
    return f"{pkg_string}"


def pack_pkg_impl(
    included_files,
    filtered_prefix,
    relocate_prefix,
    pkg_meta,
    compression_format,
    use_cache,
    compresslevel,
    cache_dir=None,
    outdir=None,
):
    if cache_dir is None:
        cache_dir = PACKED_PACKAGES_CACHE_DIR
    fname_core = f"{filename_base_from_meta(pkg_meta)}.tar.{compression_format}"
    cache_file = cache_dir / fname_core

    if outdir is not None:
        fname = os.path.join(outdir, fname_core)
    else:
        fname = fname_core

    if use_cache:
        if cache_file.exists():
            if outdir is not None:
                shutil.copy(cache_file, fname)
            return fname_core, True

    conda_meta_filename = f"{filename_base_from_meta(pkg_meta)}.json"
    with open(filtered_prefix / "conda-meta" / conda_meta_filename, "w") as f:
        json.dump(pkg_meta, f)

    # make included files absolute
    filenames = [os.path.join(filtered_prefix, f) for f in included_files]
    arcnames = [os.path.join(relocate_prefix, f) for f in included_files]

    # arcnames relative to relocate_prefix
    arcnames = [os.path.relpath(a, relocate_prefix) for a in arcnames]

    # compress the filtered environment
    save_as_tarfile(
        output_filename=fname,
        filenames=filenames,
        arcnames=arcnames,
        compression_format=compression_format,
        compresslevel=compresslevel,
    )
    # copy to cache
    shutil.copy(fname, cache_file)

    return fname_core, False


def pack_pkg(
    pkg_spec,
    relocate_prefix,
    file_filter,
    channels,
    use_cache,
    cache_dir=None,
    micromamba_exe=None,
    compression_format=ALLOWED_FORMATS[0],
    compresslevel=9,
    outdir=None,
):
    with TemporaryDirectory() as tmp_dir:
        # create the env at the temporary location
        prefix = Path(tmp_dir) / "env"
        create_environment(
            prefix=prefix,
            packages=[pkg_spec],
            relocate_prefix=relocate_prefix,
            micromamba_exe=micromamba_exe,
            channels=channels,
            no_deps=True,
            platform="emscripten-32",
        )

        # filter the env
        filtered_prefix = Path(tmp_dir) / "filtered_env"
        filtered_prefix.mkdir()
        pkg_meta = [pkg_meta for pkg_meta in iterate_env_pkg_meta(prefix)][0]

        included_files = filter_pkg(
            env_prefix=prefix,
            target_dir=filtered_prefix,
            pkg_meta=pkg_meta,
            matchers=[file_filter],
        )

        pkg_meta = [pkg_meta for pkg_meta in iterate_env_pkg_meta(filtered_prefix)][0]

        pkg_fname, used_cache = pack_pkg_impl(
            included_files=included_files,
            filtered_prefix=filtered_prefix,
            relocate_prefix=relocate_prefix,
            pkg_meta=pkg_meta,
            use_cache=use_cache,
            cache_dir=cache_dir,
            outdir=outdir,
            compression_format=compression_format,
            compresslevel=compresslevel,
        )
    return pkg_fname, used_cache


def pack_env(
    env_prefix,
    relocate_prefix,
    file_filters,
    use_cache,
    cache_dir=None,
    compression_format=ALLOWED_FORMATS[0],
    compresslevel=9,
    outdir=None,
):
    with TemporaryDirectory() as tmp_dir:
        #  filter the complete environment
        filtered_prefix = Path(tmp_dir) / "filtered_env"
        included_files = filter_env(
            env_prefix=env_prefix,
            target_dir=filtered_prefix,
            pkg_file_filter=file_filters,
        )


        packages_info = []
        for pkg_meta in iterate_env_pkg_meta(filtered_prefix):
            pack_pkg_impl(
                included_files=included_files[pkg_meta["name"]],
                filtered_prefix=filtered_prefix,
                relocate_prefix=relocate_prefix,
                pkg_meta=pkg_meta,
                use_cache=use_cache,
                outdir=outdir,
                cache_dir=cache_dir,
                compression_format=compression_format,
                compresslevel=compresslevel,
            )

            base_fname = filename_base_from_meta(pkg_meta)
            packages_info.append(
                dict(
                    name=pkg_meta["name"],
                    version=pkg_meta["version"],
                    build=pkg_meta["build"],
                    filename_stem=base_fname,
                    filename=f"{base_fname}.tar.{compression_format}",
                )
            )

        # save the list of packages
        env_meta = {
            "prefix": str(relocate_prefix),
            "packages": packages_info,
        }
        empack_env_meta_filename = "empack_env_meta.json"
        if outdir is not None:
            empack_env_meta_filename = Path(outdir) / empack_env_meta_filename
        with open(empack_env_meta_filename, "w") as f:
            json.dump(env_meta, f, indent=4)


def pack_directory(
    host_dir,
    mount_dir,
    outname,
    compression_format=ALLOWED_FORMATS[0],
    compresslevel=9,
    outdir=None,
):
    host_dir = Path(host_dir)
    if not host_dir.is_dir():
        raise RuntimeError(f"host_dir must be a directory: {host_dir=}")
    if outdir is not None:
        output_filename = Path(outdir) / outname
    else:
        output_filename = outname

    mount_dir = PosixPath(mount_dir)
    if not mount_dir.is_absolute() or mount_dir.parts[0] != "/":
        raise RuntimeError(
            f'mount_dir must be an absolute path starting with "/" eg "/usr/local" or "/foo/bar" but is: {mount_dir}'
        )

    # remove first part from mount_dir
    mount_dir = PosixPath(*mount_dir.parts[1:])
    assert mount_dir.is_absolute() is False

    # iterate over all files in host_dir and store in list
    filenames = []
    arcnames = []
    for root, dirs, files in os.walk(host_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, host_dir)
            filenames.append(os.path.join(root, file))
            if mount_dir == PosixPath("."):
                arcnames.append(rel_path)
            else:
                arcnames.append(os.path.join(mount_dir, rel_path))

    save_as_tarfile(
        output_filename=output_filename,
        filenames=filenames,
        arcnames=arcnames,
        compression_format=compression_format,
        compresslevel=compresslevel,
    )


def pack_file(
    host_file,
    mount_dir,
    outname,
    compression_format=ALLOWED_FORMATS[0],
    outdir=None,
    compresslevel=9,
):
    host_file = Path(host_file)
    if not host_file.is_file():
        raise RuntimeError(f"File {host_file} is not a file")

    mount_dir = PosixPath(mount_dir)
    if not mount_dir.is_absolute() or mount_dir.parts[0] != "/":
        raise RuntimeError(
            'mount_dir must be an absolute path starting with "/" eg "/usr/local" or "/foo/bar"'
        )

    if outdir is not None:
        output_filename = Path(outdir) / outname
    else:
        output_filename = outname

    # remove first part from mount_dir
    mount_dir = PosixPath(*mount_dir.parts[1:])
    assert mount_dir.is_absolute() is False

    save_as_tarfile(
        output_filename=output_filename,
        filenames=[host_file],
        arcnames=[mount_dir / host_file.name],
        compression_format=compression_format,
        compresslevel=compresslevel,
    )
