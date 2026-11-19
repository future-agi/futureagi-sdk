"""Derive physical namespace inventories from emitted archives, not build-dir guesses.

The catalog supplies API identities only. Case/separator normalization relates those
identities to emitted modules, including nested accessors. Every archive path is
retained verbatim: runtime formats, declarations and maps are never reconstructed.
Use --write to propose a new snapshot; review its diff before admitting a candidate.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROWS, SURFACES

EXPECTED = Path(__file__).with_name('typescript-inventory.json')
SUFFIXES = ('.d.ts.map', '.d.mts.map', '.d.cts.map', '.js.map', '.mjs.map', '.cjs.map',
            '.d.ts', '.d.mts', '.d.cts', '.js', '.mjs', '.cjs', '.ts', '.map')


def segments(value):
    return tuple(re.sub('[^a-z0-9]', '', part.lower()) for part in re.split(r'[/.]', value))


def emitted(name):
    return name.startswith('package/') and (name.startswith('package/dist/') or name.endswith(SUFFIXES))


def owners(name):
    stem = name
    for suffix in SUFFIXES:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    path = segments(stem)
    matches = {}
    for namespace, (modules, accessors, aliases, _) in SURFACES.items():
        # A bare client.gateway accessor is not the gateway data-plane module.
        # Nested accessors supply structure (agents.runs), not broad leaf matches.
        identities = {segments(n) for n in [namespace, *modules, *aliases,
                                            *(a for a in accessors if '.' in a)]}
        positions = [i for identity in identities for i in range(1, len(path) - len(identity) + 1)
                     if path[i:i + len(identity)] == identity]
        if positions:
            matches[namespace] = min(positions)
    # A gateway/models file belongs to gateway, not the top-level model catalog.
    # Keep co-owned parent/nested matches starting at the same module boundary.
    found = [n for n, position in matches.items() if position == min(matches.values())]
    if not found:
        # Core configuration is not an independently removable namespace.
        config = {'credentials', 'config', 'configuration', 'extraheaders', 'transport', 'futureagiclient'}
        found = ['config' if any(p in config for p in path) else 'install']
    return found


def module_stem(name):
    return next((name[:-len(suffix)] for suffix in SUFFIXES if name.endswith(suffix)), name)


def declared_owners(declarations):
    """Shared output modules can contain namespace classes with no namespace dir."""
    result = {}
    for path, text in declarations.items():
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        symbols = re.findall(r'\b(?:export\s+)?(?:declare\s+)?class\s+(\w+)', text)
        matches = set()
        for namespace, (modules, accessors, aliases, _) in SURFACES.items():
            identities = {segments(n)[-1] for n in [namespace, *modules, *accessors, *aliases]}
            for symbol in symbols:
                normalized = segments(re.sub(r'(?:Client|Resource)$', '', symbol))[0]
                if normalized in identities:
                    matches.add(namespace)
        result[module_stem(path)] = matches
    return result


def derive(names, declarations=None, known=None):
    rows = {name: {'id': f'N{i:02}', 'namespace': name, 'files': []}
            for i, (name, _, _) in enumerate(ROWS)}
    shared = declared_owners(declarations or {})
    pinned = {}
    # A map/declaration/runtime file retained alone keeps its reviewed ownership,
    # even if the hide removed the companion .d.ts used to discover that ownership.
    for row in (known or {}).get('namespaces', []):
        for file in row['files']:
            pinned.setdefault(file, set()).add(row['namespace'])
    for name in sorted(set(names)):
        if emitted(name):
            for owner in set(owners(name)) | shared.get(module_stem(name), set()) | pinned.get(name, set()):
                rows[owner]['files'].append(name)
    return list(rows.values())


def compare(names, policy, expected, declarations=None):
    actual = derive(names, declarations, expected)
    if [r['namespace'] for r in expected['namespaces']] != [r['namespace'] for r in actual]:
        raise ValueError('Expected inventory must cover every catalog namespace in order')
    expected_files = {f for r in expected['namespaces'] for f in r['files']}
    actual_files = {f for r in actual for f in r['files']}
    removable = {f for r in expected['namespaces'] if policy['states'].get(r['namespace'], {}).get('ts') == 'OFF'
                 for f in r['files']}
    changed_ownership = [r['namespace'] for r, previous in zip(actual, expected['namespaces'])
                         if r['id'] != previous['id'] or
                         set(r['files']) & expected_files != set(previous['files']) & actual_files]
    added = sorted(actual_files - expected_files)
    missing = sorted(expected_files - actual_files - removable)
    return {'name': 'install.typescript-inventory', 'state': 'FAIL' if added or missing or changed_ownership else 'PASS',
            'added': added, 'missing': missing, 'changed_ownership': changed_ownership}


def snapshot(tarball):
    # Archive is inspected only, never extracted or executed by this generator.
    from artifacts import names_safe
    with tarfile.open(tarball) as archive:
        members = archive.getmembers()
        names_safe([m.name for m in members])
        if any(not (m.isfile() or m.isdir()) for m in members):
            raise ValueError('Non-regular archive member')
        names = [m.name for m in members if m.isfile()]
        declarations = {name: archive.extractfile(name).read().decode('utf8') for name in names
                        if name.endswith(('.d.ts', '.d.mts', '.d.cts'))}
    return {'schema': 1, 'artifact': Path(tarball).name,
            'sha256': hashlib.sha256(Path(tarball).read_bytes()).hexdigest(),
            'namespaces': derive(names, declarations)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tarball', type=Path)
    parser.add_argument('--write', type=Path, required=True)
    args = parser.parse_args()
    args.write.write_text(json.dumps(snapshot(args.tarball), indent=2) + '\n')


if __name__ == '__main__':
    main()
