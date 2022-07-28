from enum import Enum
from pydantic import BaseModel, Field
from typing import Union, List
from pydantic import BaseModel, validator, PrivateAttr, Field, Extra
import fnmatch

import pathlib
import re


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
