import fnmatch
import re
from typing import Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Extra, Field, PrivateAttr


class FilePatternsModelBase(BaseModel, extra=Extra.forbid):
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


class FilePattern(BaseModel, extra=Extra.forbid):
    __root__: Union[RegexPattern, UnixPattern]

    def match(self, path):
        return self.__root__.match(path)


class FileFilter(BaseModel, extra=Extra.forbid):

    include_patterns: List[FilePattern] = Field(default_factory=list)
    exclude_patterns: List[FilePattern] = Field(default_factory=list)

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


class PkgFileFilter(BaseModel, extra=Extra.forbid):
    packages: Dict[str, FileFilter]
    default: FileFilter

    def match(self, pkg_name, path):
        matcher = self.packages.get(pkg_name, self.default)
        return matcher.match(path)

    def merge(self, *others):
        for other in others:
            if other.default is not None:
                self.default = other.default

            for pkg_name, filters in other.packages.items():
                self.packages[pkg_name] = filters


# when multiple config files are provided, the default
# must be optional for the additional configs, otherwise
# the would always overwrite the main default config
class AdditionalPkgFileFilter(BaseModel, extra=Extra.forbid):
    packages: Dict[str, FileFilter]
    default: Optional[FileFilter]


def pkg_file_filter_from_yaml(path, *extra_path):

    with open(path, "r") as pack_config_file:
        pack_config = yaml.safe_load(pack_config_file)
        pkg_file_filter = PkgFileFilter.parse_obj(pack_config)

    for path in extra_path:
        with open(path, "r") as pack_config_file:
            pack_config = yaml.safe_load(pack_config_file)
            pkg_file_filter.merge(AdditionalPkgFileFilter.parse_obj(pack_config))
    return pkg_file_filter
