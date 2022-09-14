import glob
import json
import os
import shutil
from pathlib import Path


def iterate_env_pkg_meta(env_prefix):
    meta_dir = os.path.join(env_prefix, "conda-meta")
    pkg_meta_files = glob.glob(os.path.join(meta_dir, "*.json"))
    for p in pkg_meta_files:
        with open(p, "r") as pkg_meta_file:
            pkg_meta = json.load(pkg_meta_file)
            yield pkg_meta


def filter_pkg(env_prefix, pkg_meta, target_dir, pkg_file_filter):

    any_file = False
    env_path = Path(env_prefix)

    name = pkg_meta["name"]
    files = pkg_meta["files"]
    for file in files:

        include = pkg_file_filter.match(path=file)
        if include:
            path = env_path / file
            if path.is_symlink() and not path.exists():
                continue

            dest_fpath = os.path.join(target_dir, file)
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copy(os.path.join(env_prefix, file), dest_fpath)
            any_file = True
    return any_file


def split_filter_pkg(env_prefix, pkg_meta, target_dirs, pkg_file_filters):
    n_pkg = len(target_dirs)
    assert n_pkg == len(pkg_file_filters)

    any_file = [False for i in range(n_pkg)]
    env_path = Path(env_prefix)

    files = pkg_meta["files"]
    for file in pkg_meta["files"]:

        for i in range(n_pkg):

            include = pkg_file_filters[i].match(path=file)
            if include:
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dirs[i], file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)
                any_file[i] = True
                break

    # add conda meta to pkg 0
    pkg_filename = f"{pkg_meta['name']}-{pkg_meta['version']}-{pkg_meta['build']}.json"
    conda_meta_target = Path(os.path.join(target_dirs[0], "conda-meta"))
    conda_meta_target.mkdir(parents=True, exist_ok=True)

    # create absolute minimum conda-meta
    pkg_conda_meta = dict(
        name=pkg_meta["name"],
        version=pkg_meta["version"],
        build=pkg_meta["build"],
        build_number=pkg_meta["build_number"],
    )
    with open(conda_meta_target / pkg_filename, "w") as f:
        json.dump(pkg_conda_meta, f)

    return any_file


def filter_env(env_prefix, target_dir, pkg_file_filter):
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        os.makedirs(target_dir)
    any_file = False

    for pkg_meta in iterate_env_pkg_meta(env_prefix):

        any_file_in_pkg = filter_pkg(
            env_prefix=env_prefix,
            pkg_meta=pkg_meta,
            target_dir=target_dir,
            pkg_file_filter=pkg_file_filter.packages.get(
                pkg_meta["name"], pkg_file_filter.default
            ),
        )
        if any_file_in_pkg:
            any_file = True
    return any_file
