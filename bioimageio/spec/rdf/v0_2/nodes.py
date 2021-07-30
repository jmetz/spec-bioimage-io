from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

from marshmallow import missing
from marshmallow.utils import _Missing

from bioimageio.spec.shared.common import DataClassFilterUnknownKwargsMixin
from bioimageio.spec.shared.nodes import Dependencies, Node, URI
from . import base_nodes

# reassign to use imported classes
Dependencies = Dependencies


@dataclass
class CiteEntry(Node, base_nodes.CiteEntry):
    pass


@dataclass
class Author(Node, base_nodes.Author):
    pass


@dataclass
class Badge(Node, base_nodes.Badge):
    pass


# to pass mypy:
# separate dataclass and abstract class as a workaround for abstract dataclasses
# from https://github.com/python/mypy/issues/5374#issuecomment-650656381
@dataclass  # use super init to allow for additional unknown kwargs
class _RDF(Node, base_nodes._RDF):
    covers: Union[_Missing, List[Path]] = missing


class RDF(_RDF, base_nodes.RDF, DataClassFilterUnknownKwargsMixin):
    def __init__(self, **kwargs):
        known_kwargs = self.get_known_kwargs(kwargs)
        super().__init__(**known_kwargs)


@dataclass
class CollectionEntry(Node, base_nodes.CollectionEntry):
    source: URI = missing


@dataclass
class ModelCollectionEntry(CollectionEntry, base_nodes.ModelCollectionEntry):
    download_url: URI = missing


@dataclass
class Collection(RDF, base_nodes.Collection):
    pass
