import json
import os
import tarfile

import pytest

from empack.file_patterns import FileFilter
from empack.micromamba_wrapper import create_environment
from empack.pack import add_tarfile_to_env_meta, pack_directory, pack_env, pack_file, pack_pkg

from .conftest import CHANNELS, FILE_FILTERS


# we use the python 3.10 package twice since we want
# to test if the caching code path is working
@pytest.mark.parametrize("pkg_spec", ["python=3.10", "numpy", "python=3.10"])
@pytest.mark.parametrize("use_cache", [False, True])
def test_pack_pkg(tmp_path, tmp_path_module, use_cache, pkg_spec):
    pkg_name = pkg_spec.split("=")[0]

    file_filter = FILE_FILTERS.get_filter_for_pkg(pkg_name)
    assert isinstance(file_filter, FileFilter)
    fname, used_cache = pack_pkg(
        pkg_spec=pkg_spec,
        relocate_prefix="/",
        channels=CHANNELS,
        file_filter=file_filter,
        outdir=tmp_path,
        use_cache=use_cache,
        cache_dir=tmp_path_module,
        compression_format="gz",
        compresslevel=1,
    )
    assert used_cache == use_cache
    assert fname.endswith(".tar.gz")
    assert fname.startswith(pkg_name)

    fname_json = fname.replace(".tar.gz", ".json")

    fname = tmp_path / fname
    assert fname.exists()

    with tarfile.open(fname, "r:gz") as tar:
        members = tar.getmembers()
        assert len(members) > 0

        meta = tar.extractfile(f"conda-meta/{fname_json}")

        pkg_meta = json.load(meta)

        assert pkg_meta["name"] == pkg_name


def test_append(tmp_path):
    # create the env at the temporary location
    prefix = tmp_path / "env"

    # create and pack env
    create_environment(
        prefix=prefix,
        packages=["python=3.10", "numpy"],
        channels=CHANNELS,
        relocate_prefix="/",
        platform="emscripten-32",
    )

    pack_env(
        env_prefix=prefix,
        outdir=tmp_path,
        use_cache=False,
        compression_format="gz",
        relocate_prefix="/",
        file_filters=FILE_FILTERS,
        compresslevel=1,
    )

    # create a directory with some files
    dir_name = "test_dir"
    dir_path = tmp_path / dir_name
    dir_path.mkdir()
    file1 = dir_path / "file1.txt"
    file1.write_text("file1")

    pack_directory(host_dir=dir_path, mount_dir="/", outname="packaged_dir.tar.gz", outdir=tmp_path)

    # append the directory to the env
    add_tarfile_to_env_meta(env_meta_filename=tmp_path, tarfile=tmp_path / "packaged_dir.tar.gz")

    # check that there is a json with all the packages
    env_metadata_json_path = tmp_path / "empack_env_meta.json"
    assert env_metadata_json_path.exists()

    with open(env_metadata_json_path) as f:
        env_meta = json.load(f)
    packages = env_meta["packages"]
    env_meta_dict = dict()

    for pkg in packages:
        env_meta_dict[pkg["filename"]] = pkg

    assert "packaged_dir.tar.gz" in env_meta_dict


@pytest.mark.parametrize("packages", [["python=3.10", "numpy"]])
@pytest.mark.parametrize("relocate_prefix", ["/", "/some/dir", "/home/some_dir/"])
def test_pack_env(tmp_path, packages, relocate_prefix):
    # create the env at the temporary location
    prefix = tmp_path / "env"

    create_environment(
        prefix=prefix,
        packages=packages,
        channels=CHANNELS,
        relocate_prefix=relocate_prefix,
        platform="emscripten-32",
    )

    pack_env(
        env_prefix=prefix,
        outdir=tmp_path,
        use_cache=False,
        compression_format="gz",
        relocate_prefix=relocate_prefix,
        file_filters=FILE_FILTERS,
        compresslevel=1,
    )

    # check that there is a json with all the packages
    env_metadata_json_path = tmp_path / "empack_env_meta.json"
    assert env_metadata_json_path.exists()

    # check that json file contains all packages
    with open(env_metadata_json_path) as f:
        env_metadata = json.load(f)
        packages_metadata = env_metadata["packages"]
        prefix = env_metadata["prefix"]
        assert prefix == relocate_prefix
        assert len(packages_metadata) >= len(packages)

        for pkg in packages:
            pkg_name = pkg.split("=")[0]

            found = False
            for pkg_meta in packages_metadata:
                if pkg_meta["name"] == pkg_name:
                    found = True
                    break
            assert found, f"Could not find package {pkg} in {packages_metadata}"

    # check that there is a tar.gz file for each package
    for pkg_info in packages_metadata:
        assert pkg_info["filename"].endswith(".tar.gz")
        fname = tmp_path / pkg_info["filename"]
        assert fname.exists()

        with tarfile.open(fname, "r:gz") as tar:
            members = tar.getmembers()
            assert len(members) > 0

            json_filename = pkg_info["filename_stem"] + ".json"
            meta = tar.extractfile(f"conda-meta/{json_filename}")
            pkg_meta = json.load(meta)
            assert pkg_info["name"] == pkg_meta["name"]


@pytest.mark.parametrize("mount_dir", ["/some", "/some/", "/some/nested", "/"])
def test_pack_directory(tmp_path, mount_dir):
    # create a directory with some files
    dir_name = "test_dir"
    dir_path = tmp_path / dir_name
    dir_path.mkdir()

    # create toplevel files
    file1 = dir_path / "file1.txt"
    file1.write_text("file1")

    file2 = dir_path / "file2.txt"
    file2.write_text("file2")

    # create some nested directories
    nested_dir = dir_path / "nested_dir_a" / "nested_dir_b"
    nested_dir.mkdir(parents=True)

    # add a file to the nested directory
    nested_file = nested_dir / "nested_file.txt"
    nested_file.write_text("nested_file")

    pack_directory(
        host_dir=dir_path,
        mount_dir=mount_dir,
        outdir=tmp_path,
        outname="packed.tar.gz",
        compresslevel=1,
    )

    # check that "packed.tar.gz" exists
    packed_file = tmp_path / "packed.tar.gz"
    assert packed_file.exists()

    # open the tar file and check that the files are there
    with tarfile.open(packed_file, "r:gz") as tar:
        file = tar.extractfile(os.path.join(mount_dir[1:], "file1.txt"))
        assert file.read().decode("utf-8") == "file1"

        file = tar.extractfile(os.path.join(mount_dir[1:], "file2.txt"))
        assert file.read().decode("utf-8") == "file2"

        file = tar.extractfile(
            os.path.join(mount_dir[1:], "nested_dir_a", "nested_dir_b", "nested_file.txt")
        )
        assert file.read().decode("utf-8") == "nested_file"


@pytest.mark.parametrize("mount_dir", ["/some", "/some/", "/some/nested", "/"])
def test_pack_file(tmp_path, mount_dir):
    # create a directory with some files
    dir_name = "test_dir"
    dir_path = tmp_path / dir_name
    dir_path.mkdir()

    # create toplevel files
    file1 = dir_path / "file1.txt"
    file1.write_text("file1")

    file2 = dir_path / "file2.txt"
    file2.write_text("file2")

    # create some nested directories
    nested_dir = dir_path / "nested_dir_a" / "nested_dir_b"
    nested_dir.mkdir(parents=True)

    # add a file to the nested directory
    nested_file = nested_dir / "nested_file.txt"
    nested_file.write_text("nested_file")

    pack_file(
        host_file=nested_file,
        mount_dir=mount_dir,
        outdir=tmp_path,
        outname="packed.tar.gz",
    )

    # check that "packed.tar.gz" exists
    packed_file = tmp_path / "packed.tar.gz"
    assert packed_file.exists()

    # open the tar file and check that the files are there
    with tarfile.open(packed_file, "r:gz") as tar:
        # print all names
        assert len(tar.getmembers()) == 1

        if mount_dir == "/":
            file = tar.extractfile("nested_file.txt")
        else:
            file = tar.extractfile(os.path.join(mount_dir[1:], "nested_file.txt"))
        assert file.read().decode("utf-8") == "nested_file"
