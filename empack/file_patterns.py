import fnmatch
import re
from typing import Optional, Union

import yaml
from pydantic import BaseModel, Field, PrivateAttr, RootModel


class FilePatternsModelBase(BaseModel, extra="forbid"):
    pass


# match based on a regex
class RegexPattern(FilePatternsModelBase):
    regex: str
    _pattern: str = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._pattern = re.compile(data["regex"])

    def match(self, path):
        return self._pattern.match(path) is not None


class UnixPattern(FilePatternsModelBase):
    pattern: str

    def match(self, path):
        return fnmatch.fnmatch(path, self.pattern)


class FilePattern(RootModel, extra="forbid"):
    root: Union[RegexPattern, UnixPattern]

    def match(self, path):
        return self.root.match(path)


class FileFilter(BaseModel, extra="forbid"):
    include_patterns: list[FilePattern] = Field(default_factory=list)
    exclude_patterns: list[FilePattern] = Field(default_factory=list)

    def match(self, path):
        include = False
        for ip in self.include_patterns:
            if ip.match(path):
                include = True
        if include:
            for ep in self.exclude_patterns:
                if ep.match(path):
                    return False

        return include


class PkgFileFilter(BaseModel, extra="forbid"):
    packages: dict[str, Union[FileFilter, list[FileFilter]]]
    default: FileFilter

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


# when multiple config files are provided, the default
# must be optional for the additional configs, otherwise
# the would always overwrite the main default config
class AdditionalPkgFileFilter(BaseModel, extra="forbid"):
    packages: dict[str, Union[FileFilter, list[FileFilter]]]
    default: Optional[FileFilter] = None


def pkg_file_filter_from_yaml(path, *extra_path):
    with open(path) as pack_config_file:
        pack_config = yaml.safe_load(pack_config_file)
        pkg_file_filter = PkgFileFilter.model_validate(pack_config)

    for path in extra_path:
        with open(path) as pack_config_file:
            pack_config = yaml.safe_load(pack_config_file)
            pkg_file_filter.merge(AdditionalPkgFileFilter.model_validate(pack_config))
    return pkg_file_filter
