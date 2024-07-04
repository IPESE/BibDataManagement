# Let users know if they're missing any of our hard dependencies
_hard_dependencies = ("pandas", "pybtex")
_missing_dependencies = []

for _dependency in _hard_dependencies:
    try:
        __import__(_dependency)
    except ImportError as _e:  # pragma: no cover
        _missing_dependencies.append(f"{_dependency}: {_e}")

if _missing_dependencies:  # pragma: no cover
    raise ImportError(
        "Unable to import required dependencies:\n" + "\n".join(_missing_dependencies)
    )
del _hard_dependencies, _dependency, _missing_dependencies

from bibdatamanagement.bibdatamanagement import BibDataManagement
from bibdatamanagement.user_interface import RBibData
from bibdatamanagement.utilities import get_file
from bibdatamanagement.md_display import MdDisplay

__all__ = [
    "BibDataManagement",
    "RBibData",
    "get_file",
    "MdDisplay"
]

__doc__ = """
bibdatamanagement - A library to enable an easy manipulation of a .bib file, with data added in the note field
===============================================================================================================
The package works really well combined with Zotero, which allows for a group to have a common bibliography and a common
place to store values for a model. 
"""