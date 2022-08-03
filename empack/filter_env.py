import glob
import json
import os
import shutil
from pathlib import Path


def filter_pkg(env_prefix, pkg_meta_file, target_dir, pkg_file_filter):

    env_path = Path(env_prefix)
    with open(pkg_meta_file, "r") as f:
        pkg_meta = json.load(f)
        name = pkg_meta["name"]
        files = pkg_meta["files"]
        for file in files:

            include = pkg_file_filter.match(pkg_name=name, path=file)
            if include:
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dir, file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)


def filter_env(env_prefix, target_dir, pkg_file_filter):
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        os.makedirs(target_dir)

    meta_dir = os.path.join(env_prefix, "conda-meta")
    pkg_meta_files = glob.glob(os.path.join(meta_dir, "*.json"))
    for pkg_meta_file in pkg_meta_files:
        filter_pkg(
            env_prefix=env_prefix,
            pkg_meta_file=pkg_meta_file,
            target_dir=target_dir,
            pkg_file_filter=pkg_file_filter,
        )
