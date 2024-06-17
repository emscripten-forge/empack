from empack.file_patterns import FileFilter, UnixPattern, pkg_file_filter_from_yaml


def test_unix_pattern():
    fp = UnixPattern(pattern="*.py")
    assert fp.match("/home/fu/bar.py")
    assert not fp.match("/hometests/fu/bar.pyc")

    fp = UnixPattern(pattern="**/tests/*")
    assert fp.match("/home/tests/bar")
    assert not fp.match("/home/fu/bar")


def test_file_filter():
    fp = FileFilter(
        exclude_patterns=[dict(pattern="**/tests/*")],
    )
    assert fp.match(
        "/tmp/xeus-python-kernel/envs/xeus-python-kernel/lib/python3.10/"  # noqa: S108
        "site-packages/matplotlib/mpl-data/matplotlibrc"
    )
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_empty_file_filter():
    fp = FileFilter(exclude_patterns=[])
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert fp.match("/home/tests/fu/bar.py")
    assert fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_dataset_filter():
    fp = FileFilter(
        exclude_patterns=[],
    )
    assert fp.match("/home/fu/sklearn/datasets/some/folder.txt")
    assert fp.match("/home/fu/sklearn/datasets/some/folder.py")
    assert fp.match("/home/fu/sxklearn/datasets/some/folder.txt")


def test_from_yaml():
    import os

    dn = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dn, "empack_test_config.yaml")
    pkg_file_filter = pkg_file_filter_from_yaml(config_path)

    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(path="/home/fu/bar.py")
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(path="/home/fu/bar.so")
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/home/tests/fu/bar.py"
    )
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/home/tests/fu/bar.so"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/hometests/fu/bar.py"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/hometests/fu/bar.so"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="scikit-image")[0].match(
        path="/home/fu/bar.py"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="scikit-image")[0].match(
        path="/home/fu/bar.so"
    )


def test_from_yaml_with_multiple():
    import os

    dn = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dn, "empack_test_config.yaml")
    extra_config_path = os.path.join(dn, "empack_test_extra_config.yaml")
    pkg_file_filter = pkg_file_filter_from_yaml(config_path, extra_config_path)

    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(path="/home/fu/bar.py")
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(path="/home/fu/bar.so")
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/home/tests/fu/bar.py"
    )
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/home/tests/fu/bar.so"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/hometests/fu/bar.py"
    )
    assert pkg_file_filter.get_filters_for_pkg(pkg_name="fubar")[0].match(
        path="/hometests/fu/bar.so"
    )
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="scikit-image")[0].match(
        path="/home/fu/bar.py"
    )
    assert not pkg_file_filter.get_filters_for_pkg(pkg_name="scikit-image")[0].match(
        path="/home/fu/bar.so"
    )


if __name__ == "__main__":
    import sys

    import pytest

    retcode = pytest.main()
    sys.exit(retcode)
