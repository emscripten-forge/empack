import glob
import json
import os
import shutil
from pathlib import Path

import yaml

from .file_patterns import FileFilter

# sensible default
pack_config = {
    "packages": {
        "python-dateutil": {
            "include_patterns": [
                {
                    "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))|(.*dateutil-zoneinfo\.tar\.gz$)",  # noqa: E501
                }
            ],
            "exclude_patterns": [],
        },
        "matplotlib": {
            "include_patterns": [
                {
                    "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))",
                },
                {"pattern": "**/matplotlib/mpl-data/**"},
            ],
            "exclude_patterns": [],
        },
        "scikit-learn": {
            "include_patterns": [
                {
                    "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))",
                },
                {"pattern": "**/sklearn/datasets/**"},
            ],
            "exclude_patterns": [],
        },
        "scikit-image": {
            "include_patterns": [
                {
                    "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))",
                },
                {"pattern": "**/skimage/data/**"},
            ],
            "exclude_patterns": [],
        },
    },
    "default": {
        "include_patterns": [
            {
                "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))",
            }
        ],
        "exclude_patterns": [],
    },
}


# load config
pack_config_path = os.path.join(os.path.expanduser("~"), "conda_pack_config.yaml")
if os.path.isfile(pack_config_path):
    with open(pack_config_path) as pack_config_file:
        pack_config = yaml.safe_load(pack_config_file)


def filter_pkg(env_prefix, pkg_meta_file, target_dir):
    env_path = Path(env_prefix)
    with open(pkg_meta_file, "r") as f:
        pkg_meta = json.load(f)
        name = pkg_meta["name"]

        if name in pack_config["packages"]:
            include_patterns = FileFilter.parse_obj(pack_config["packages"][name])
        else:
            include_patterns = FileFilter.parse_obj(pack_config["default"])

        files = pkg_meta["files"]
        for file in files:
            include = include_patterns.match(file)
            if include:
                path = env_path / file
                if path.is_symlink() and not path.exists():
                    continue

                dest_fpath = os.path.join(target_dir, file)
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(os.path.join(env_prefix, file), dest_fpath)


def filter_env(env_prefix, target_dir):
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
        os.makedirs(target_dir)

    meta_dir = os.path.join(env_prefix, "conda-meta")
    pkg_meta_files = glob.glob(os.path.join(meta_dir, "*.json"))
    for pkg_meta_file in pkg_meta_files:
        filter_pkg(
            env_prefix=env_prefix, pkg_meta_file=pkg_meta_file, target_dir=target_dir
        )
