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


def filter_pkg(env_prefix, pkg_meta, target_dir, matchers):

    any_file = False
    env_path = Path(env_prefix)

    name = pkg_meta["name"]
    files = pkg_meta["files"]
    for file in files:

        for i, matcher in enumerate(matchers):

            include = matcher.match(path=file)
            if include:
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dir, file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)
                any_file = True
                break
    return any_file


def split_filter_pkg(env_prefix, pkg_meta, target_dirs, matchers):

    assert len(target_dirs) == len(matchers)

    any_files_array = [False] * len(target_dirs)
    env_path = Path(env_prefix)

    name = pkg_meta["name"]
    files = pkg_meta["files"]
    for file in files:

        for i, matcher in enumerate(matchers):

            include = matcher.match(path=file)
            if include:
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dirs[i], file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)
                any_files_array[i] = True

                break

    return any_files_array


def filter_env(env_prefix, target_dir, pkg_file_filter):
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        os.makedirs(target_dir)
    any_file = False
    for pkg_meta in iterate_env_pkg_meta(env_prefix):

        matchers = pkg_file_filter.get_matchers(pkg_name=pkg_meta["name"])

        any_file_in_pkg = filter_pkg(
            env_prefix=env_prefix,
            pkg_meta=pkg_meta,
            target_dir=target_dir,
            matchers=matchers,
        )
        if any_file_in_pkg:
            any_file = True
    return any_file
