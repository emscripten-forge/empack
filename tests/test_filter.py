from empack.file_patterns import FileFilter, FilePattern


def test_regex_pattern():
    fp = FilePattern.parse_obj(
        {
            "regex": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))|(.*dateutil-zoneinfo\.tar\.gz$)",
        }
    )
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_unix_pattern():
    fp = FilePattern.parse_obj({"pattern": "*.py"})
    assert fp.match("/home/fu/bar.py")
    assert not fp.match("/hometests/fu/bar.pyc")

    fp = FilePattern.parse_obj({"pattern": "**/tests/*"})
    assert fp.match("/home/tests/bar")
    assert not fp.match("/home/fu/bar")


def test_file_filter():
    fp = FileFilter.parse_obj(
        {
            "include_patterns": [{"pattern": "*.py"}, {"pattern": "*.so"}],
            "exclude_patterns": [{"pattern": "**/tests/*"}],
        }
    )

    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_empty_file_filter():

    fp = FileFilter.parse_obj({"include_patterns": [], "exclude_patterns": []})
    assert not fp.match("/home/fu/bar.py")
    assert not fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert not fp.match("/hometests/fu/bar.py")
    assert not fp.match("/hometests/fu/bar.so")


if __name__ == "__main__":
    import sys

    import pytest

    retcode = pytest.main()
    sys.exit(retcode)
