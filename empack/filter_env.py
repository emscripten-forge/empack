import csv
import glob
import json
import os
import shutil
from pathlib import Path


def iterate_pip_pkg_record(env_prefix):
    # Find all RECORD files for .dist-info folders for which INSTALLER is "pip"
    # Resolve site-packages directory, ignoring the python3.1/ symlink
    prefix = Path(env_prefix).resolve()

    site_packages = [
        site_package
        for site_package in prefix.glob("lib/python*/site-packages")
        if "python3.1" not in site_package.parts
    ]
    if not site_packages:
        return []
    site_packages = site_packages[0]
    relative_site_packages = site_packages.relative_to(prefix)

    packages_dist_info = Path(site_packages).resolve().glob("*.dist-info")

    for dist_info in packages_dist_info:
        if not (dist_info / "INSTALLER").exists():
            continue

        # Continue if package not installed with pip
        with open(dist_info / "INSTALLER") as installer:
            if installer.read().strip() != "pip":
                continue

        # Fetch package name
        package_name, package_version = dist_info.name.removesuffix(".dist-info").split("-")

        # Find all files
        with open(dist_info / "RECORD") as record:
            files = csv.reader(record)
            all_files = [_file[0] for _file in files]
            all_files_paths = [
                relative_site_packages / _file
                for _file in all_files
                # Excluding .dist-info files
                if ".dist-info" not in _file
            ]

        yield dict(
            name=package_name,
            version=package_version,
            files=all_files_paths,
            # Some hugly hacks to make it work...
            fn=f"{package_name}-{package_version}",
            build="pip",
            build_number=0,
            depends=[],
        )


def iterate_env_pkg_meta(env_prefix):
    meta_dir = os.path.join(env_prefix, "conda-meta")
    pkg_meta_files = glob.glob(os.path.join(meta_dir, "*.json"))

    for p in pkg_meta_files:
        with open(p) as pkg_meta_file:
            pkg_meta = json.load(pkg_meta_file)
            yield pkg_meta

    # Iterate through pip installed packages and get mock pkg_meta
    for pkg_meta in iterate_pip_pkg_record(env_prefix):
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
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dir, file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                try:
                    shutil.copy(os.path.join(env_prefix, file), dest_fpath)
                    included.append(file)
                except FileNotFoundError:
                    # This may happen when following a symlink on a filtered out file
                    pass
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
