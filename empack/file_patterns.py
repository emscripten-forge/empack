from enum import Enum
from pydantic import BaseModel, Field
from typing import Union, List
from pydantic import BaseModel, validator, PrivateAttr, Field, Extra

import pathlib
import re


class FilePatternsModelBase(BaseModel, extra=Extra.forbid):
    type: str


# match based on a list of extensions
class ExtensionsPattern(FilePatternsModelBase):
    extensions: List[str]

    @validator("type")
    def check_type(cls, v):
        if v != "extensions":
            raise ValueError("not an ExtensionsPattern")
        return v

    def match(self, path):
        return pathlib.Path(path).suffix in self.extensions


# match based on a regex
class RegexPattern(FilePatternsModelBase):
    pattern: str
    _pattern: str = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._pattern = re.compile(data["pattern"])

    @validator("type")
    def check_type(cls, v):
        if v != "regex":
            raise ValueError("not a RegexPattern")
        return v

    def match(self, path):
        return self._pattern.match(path) is not None


# matches everything
class AnyPattern(FilePatternsModelBase):
    @validator("type")
    def check_type(cls, v):
        if v != "any":
            raise ValueError("not a AnyPattern")
        return v

    def match(self, path):
        return True


# match if a path contains any string rom a list of strings
class ContainsAnyPattern(FilePatternsModelBase):
    contains_any: List[str]

    @validator("type")
    def check_type(cls, v):
        if v != "contains_any":
            raise ValueError("not a ContainsAnyPattern")
        return v

    def match(self, path):
        for s in self.contains_any:
            if s in path:
                return True
        return False


class FilePattern(BaseModel, extra=Extra.forbid):
    __root__: Union[RegexPattern, ExtensionsPattern, ContainsAnyPattern, AnyPattern]

    def match(self, path):
        return self.__root__.match(path)


class FileFilter(BaseModel, extra=Extra.forbid):

    include_patterns: List[FilePattern] = Field(default_factory=list)
    exclude_patterns: List[FilePattern] = Field(default_factory=list)

    def match(self, path):
        for ip in self.include_patterns:
            if not ip.match(path):
                return False
        for ep in self.exclude_patterns:
            if ep.match(path):
                return False

        return True
