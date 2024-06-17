import fnmatch
import re

import yaml


class RegexPattern:
    def __init__(self, regex):
        self._pattern = re.compile(regex)

    def match(self, path):
        return self._pattern.match(path) is not None


class UnixPattern:
    def __init__(self, pattern):
        self.pattern = pattern

    def match(self, path):
        return fnmatch.fnmatch(path, self.pattern)


class FileFilter:
    def __init__(self, include_patterns=None, exclude_patterns=None):
        def patter_from_dict(**d):
            if "pattern" in d:
                return UnixPattern(**d)
            elif "regex" in d:
                return RegexPattern(**d)
            else:
                raise ValueError("pattern or regex must be provided")

        if exclude_patterns is None:
            exclude_patterns = []
        self.exclude_patterns = [patter_from_dict(**p) for p in exclude_patterns]

    def match(self, path):
        return all(not ep.match(path) for ep in self.exclude_patterns)


class PkgFileFilter:
    def __init__(self, packages=None, default=None):
        self.packages = {}

        if packages is None:
            packages = {}

        default_exclude_patterns = []
        if default is not None and "exclude_patterns" in default:
            default_exclude_patterns = default["exclude_patterns"]

        for k, v in packages.items():
            if isinstance(v, dict):
                exclude_patterns = default_exclude_patterns
                if "exclude_patterns" in v:
                    exclude_patterns = exclude_patterns + v["exclude_patterns"]
                self.packages[k] = FileFilter(exclude_patterns=exclude_patterns)
            else:
                err = f"invalid value for package {k}: {v}"
                raise ValueError(err)

        if default is not None:
            self.default = FileFilter(**default)
        else:
            self.default = None

    def get_filter_for_pkg(self, pkg_name):
        return self.packages.get(pkg_name, self.default)

    def get_filters_for_pkg(self, pkg_name):
        matchers = self.get_filter_for_pkg(pkg_name)
        if not isinstance(matchers, list):
            matchers = [matchers]
        return matchers

    def merge(self, *others):
        for other in others:
            if other.default is not None:
                self.default = other.default

            for pkg_name, filters in other.packages.items():
                self.packages[pkg_name] = filters


def pkg_file_filter_from_yaml(path, *extra_path):
    with open(path) as pack_config_file:
        pack_config = yaml.safe_load(pack_config_file)
        pkg_file_filter = PkgFileFilter(**pack_config)

    for path in extra_path:
        with open(path) as pack_config_file:
            pack_config = yaml.safe_load(pack_config_file)
            additonal_pkg_file_filter = PkgFileFilter(**pack_config)
            pkg_file_filter.merge(additonal_pkg_file_filter)
    return pkg_file_filter
