"""Synchronize only manifest-owned P0 files, preserving unrelated SDK work.

Existing owned files must still match their recorded hashes before any write.
New files never overwrite unrelated content. The target receives its own role
and exact SDK workflow, then a fresh source inventory. No Git/API mutation.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync(target):
    target=target.resolve()
    if not (target/'src/finger_trader/strategy/base.py').is_file():
        raise ValueError('not an SDK checkout')
    source=json.loads((ROOT/'ci/quant-files.json').read_text())
    for rel,expected in source['files'].items():
        if digest(ROOT/rel)!=expected:
            raise ValueError('source inventory is stale: '+rel)
    old_path=target/'ci/quant-files.json'
    old=json.loads(old_path.read_text())['files'] if old_path.exists() else {}
    for rel,expected in old.items():
        path=target/rel
        if path.resolve()!=path.absolute() or path.is_symlink() or digest(path)!=expected:
            raise ValueError('owned target changed independently: '+rel)
    pairs={rel:(ROOT/rel).read_bytes() for rel in source['files'] if rel != 'ci/quant-peer.json'}
    pairs['ci/quant-role.json']=b'{"role":"sdk"}\n'
    pairs['.github/workflows/quant-contracts.yml']=(ROOT/'tools/quant/sdk-quant-contracts.yml').read_bytes()
    for rel,data in pairs.items():
        path=target/rel
        if path.resolve()!=path.absolute() or path.is_symlink():
            raise ValueError('unsafe target: '+rel)
        if path.exists() and rel not in old and path.read_bytes()!=data:
            raise ValueError('unowned target exists: '+rel)
    for rel,data in pairs.items():
        path=target/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest={**source,'files':{rel:hashlib.sha256(data).hexdigest() for rel,data in pairs.items()}}
    old_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Synced manifest-owned candidate:',len(pairs),'files')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk',required=True,type=Path)
    sync(parser.parse_args().sdk)
