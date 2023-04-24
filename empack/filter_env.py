import glob
import json
import os
import shutil
from pathlib import Path


def iterate_env_pkg_meta(env_prefix):
    meta_dir = os.path.join(env_prefix, "conda-meta")
    pkg_meta_files = glob.glob(os.path.join(meta_dir, "*.json"))
    for p in pkg_meta_files:
        with open(p) as pkg_meta_file:
            pkg_meta = json.load(pkg_meta_file)
            yield pkg_meta


def write_minimal_conda_meta(pkg_meta, env_prefix):
    content = {k: pkg_meta[k] for k in ["name", "version", "build", "build_number"]}
    conda_meta_dir = Path(env_prefix) / "conda-meta"
    conda_meta_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{pkg_meta['name']}-{pkg_meta['version']}-{pkg_meta['build']}.json"
    path = conda_meta_dir / filename
    with open(path, "w") as f:
        json.dump(content, f)
    return path


def filter_pkg(env_prefix, pkg_meta, target_dir, matchers):
    included = []
    env_path = Path(env_prefix)
    files = pkg_meta["files"]
    for file in files:
        for _i, matcher in enumerate(matchers):
            include = matcher.match(path=file)
            if include:
                included.append(file)
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dir, file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)
                break
    path = write_minimal_conda_meta(pkg_meta=pkg_meta, env_prefix=target_dir)
    included.append(path.relative_to(target_dir))
    return included


def filter_env(env_prefix, target_dir, pkg_file_filter, verbose=0):
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        os.makedirs(target_dir)

    per_pkg_included_files = {}
    for pkg_meta in iterate_env_pkg_meta(env_prefix):
        if verbose > 0:
            print(f"filtering {pkg_meta['name']}")
        file_filter = pkg_file_filter.get_filters_for_pkg(pkg_name=pkg_meta["name"])

        included_files = filter_pkg(
            env_prefix=env_prefix,
            pkg_meta=pkg_meta,
            target_dir=target_dir,
            matchers=file_filter,
        )
        per_pkg_included_files[pkg_meta["name"]] = included_files

    return per_pkg_included_files
