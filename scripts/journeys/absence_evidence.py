"""The complete installed-consumer absence contract, not any matching check."""


def runtimes(language):
    if language == 'py':
        return [f'py-{v}-{extra}' for v in ('3.10', '3.12') for extra in ('base', 'evals', 'tracing')]
    return ['ts-20', 'ts-22']


def required(namespace, spec, language):
    prefix = 'absence.' + namespace + '.'
    if language == 'py':
        suffixes = ['import.fi.' + m for m in spec['py_modules']]
        suffixes += ['accessor.' + client + '.' + a for client in ('FutureAGIClient', 'AsyncFutureAGIClient')
                     for a in spec['py_accessors']]
        suffixes += ['root.' + m for m in spec['py_modules'] if '.' not in m]
        suffixes += ['root-export.' + s for s in spec['root_exports']]
        suffixes += ['cli']
    else:
        suffixes = [mode + '.' + kind + '.' + name for mode in ('esm', 'cjs')
                    for kind, names in (('subpath', spec['ts_subpaths']), ('accessor', spec['ts_accessors']),
                                        ('root-export', spec['root_exports'])) for name in names]
    return [prefix + name for name in suffixes]


def complete(checks, names, runtime):
    rows = [{**check, 'runtime': runtime} for check in checks]
    found = {check['name'] for check in checks}
    rows.extend({'name': name, 'state': 'NOT-EVALUATED', 'runtime': runtime,
                 'reason': 'Missing required absence evidence'} for name in names if name not in found)
    return rows


def collect(namespace, language, policy, probes, archive):
    prefix = 'absence.' + namespace + '.'
    names = [prefix + n for n in (('archive', 'docs') if language == 'py' else ('archive', 'export-map', 'docs'))]
    rows = complete([c for c in archive.get(language, []) if c['name'].startswith(prefix)], names, 'archive-' + language)
    names = required(namespace, policy['surfaces'][namespace], language)
    prerequisites = ['install.probe'] if language == 'py' else ['install.esm.probe', 'install.cjs.probe']
    for runtime in runtimes(language):
        checks = probes.get(runtime, {}).get('checks', [])
        rows.extend(complete([c for c in checks if c['name'].startswith(prefix)], names, runtime))
        install = {c['name']: c['state'] for c in checks if c['name'].startswith('install.')}
        if any(install.get(name) != 'PASS' for name in prerequisites) or any(s != 'PASS' for s in install.values()):
            rows.append({'name': prefix + 'runtime-prerequisite', 'state': 'NOT-EVALUATED', 'runtime': runtime,
                         'reason': 'Required consumer installation/import evidence is missing or unsuccessful'})
    return rows
