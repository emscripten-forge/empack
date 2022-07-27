from empack.file_patterns import *


def test_extension_pattern():
    fp = FilePattern.parse_obj({"type": "extensions", "extensions": [".so", ".py"]})
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert fp.match("fop.bar.py")
    assert fp.match("fop.bar.so")
    assert not fp.match("/home/fu/bar.png")
    assert not fp.match("/home/fu/bar.jpeg")
    assert not fp.match("/home/fubarpy")
    assert not fp.match("/home/fubarso")


def test_regex_pattern():
    fp = FilePattern.parse_obj(
        {
            "type": "regex",
            "pattern": R"^(?!.*\/tests\/).*((.*.\.py$)|(.*.\.so$))|(.*dateutil-zoneinfo\.tar\.gz$)",
        }
    )
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_contains_any_pattern():
    fp = FilePattern.parse_obj(
        {"type": "contains_any", "contains_any": ["tests/", "other/"]}
    )
    assert not fp.match("/home/testsfu/bar.py")
    assert not fp.match("/home/testsfu/bar.so")
    assert fp.match("/home/tests/fu/bar.py")
    assert fp.match("/home/tests/fu/bar.so")
    assert fp.match("/home/other/fu/bar.py")
    assert fp.match("/home/other/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_file_filter():
    fp = FileFilter.parse_obj(
        {
            "include_patterns": [{"type": "extensions", "extensions": [".so", ".py"]}],
            "exclude_patterns": [{"type": "contains_any", "contains_any": ["/tests/"]}],
        }
    )

    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


def test_any_file_filter():
    fp = FileFilter.parse_obj(
        {"include_patterns": [{"type": "any"}], "exclude_patterns": []}
    )

    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert fp.match("/home/tests/fu/bar.py")
    assert fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")

    fp = FileFilter.parse_obj(
        {"exclude_patterns": [{"type": "any"}], "include_patterns": []}
    )

    assert not fp.match("/home/fu/bar.py")
    assert not fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert not fp.match("/hometests/fu/bar.py")
    assert not fp.match("/hometests/fu/bar.so")

    fp = FileFilter.parse_obj(
        {"include_patterns": [{"type": "any"}], "exclude_patterns": [{"type": "any"}]}
    )

    assert not fp.match("/home/fu/bar.py")
    assert not fp.match("/home/fu/bar.so")
    assert not fp.match("/home/tests/fu/bar.py")
    assert not fp.match("/home/tests/fu/bar.so")
    assert not fp.match("/hometests/fu/bar.py")
    assert not fp.match("/hometests/fu/bar.so")


def test_empty_file_filter():
    fp = FileFilter.parse_obj(
        {"include_patterns": [{"type": "any"}], "exclude_patterns": []}
    )
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert fp.match("/home/tests/fu/bar.py")
    assert fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")

    fp = FileFilter.parse_obj({"include_patterns": [], "exclude_patterns": []})
    assert fp.match("/home/fu/bar.py")
    assert fp.match("/home/fu/bar.so")
    assert fp.match("/home/tests/fu/bar.py")
    assert fp.match("/home/tests/fu/bar.so")
    assert fp.match("/hometests/fu/bar.py")
    assert fp.match("/hometests/fu/bar.so")


if __name__ == "__main__":
    import pytest
    import sys

    retcode = pytest.main()
    sys.exit(retcode)
