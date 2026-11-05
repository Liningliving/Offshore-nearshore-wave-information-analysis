"""Resolve historical artifact paths without rewriting archived provenance.

Current scripts use descriptive paths directly. This helper is for saved CSV/JSON
references written before the directory/entry-point rename. Source hashes in old
manifests still describe the original source revision, not today's renamed code.
"""
from functools import lru_cache
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAPPINGS=(ROOT/'config/legacy_paths.json',)

@lru_cache(maxsize=1)
def _renames():
    result={}
    for mapping in MAPPINGS:
        data=json.loads(mapping.read_text())
        result.update(data)
    return sorted(result.items(),key=lambda pair:-len(pair[0]))

def resolve_artifact_path(value):
    """Resolve archived paths through all recorded layout migrations."""
    path=Path(value)
    if path.is_absolute():
        try:relative=path.relative_to(ROOT).as_posix()
        except ValueError:return path
    else:relative=path.as_posix()
    seen=set()
    while True:
        if relative in seen:raise ValueError('Cycle in artifact path migrations')
        seen.add(relative)
        for old,new in _renames():
            if relative==old or relative.startswith(old+'/'):
                relative=new+relative[len(old):]
                break
        else:return ROOT/relative
