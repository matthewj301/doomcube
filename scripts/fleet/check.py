#!/usr/bin/env python3
"""Read-only fleet source audit. Not a Klipper parser or deployment gate."""
import argparse
import ast
import glob
import hashlib
import json
import re
from pathlib import Path

SECTION = re.compile(r'^\s*\[([^]\n]+)\]\s*(?:[#;].*)?$')
OPTION = re.compile(r'^([^\s#;][^:=]*?)\s*[:=]\s*(.*)$')
PARAM = re.compile(r'''params(?:\.([A-Z][A-Z0-9_]*)|\.get\(["']([A-Z][A-Z0-9_]*)["']|\[["']([A-Z][A-Z0-9_]*)["']\])''')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan(root, entry, config_root):
    root = Path(root).resolve()
    result = {'files': [], 'unresolved': [], 'cycles': [], 'duplicate_sections': [],
              'python_errors': [], 'literal_errors': [], 'macros': {}, 'save_variables': []}
    sections = {}
    visited = set()

    def walk(path, stack):
        path = Path(path)
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            result['unresolved'].append({'path': str(path), 'reason': 'external path or symlink'})
            return
        if not path.is_file():
            result['unresolved'].append({'path': str(path), 'reason': 'missing file or dangling symlink'})
            return
        key = str(resolved.relative_to(root))
        if resolved in stack:
            result['cycles'].append(key)
            return
        # Repeated inclusion still matters for duplicate definitions; only the
        # active recursion stack suppresses cycles.
        if key not in visited:
            result['files'].append(key)
            visited.add(key)
        current = None
        for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
            match = SECTION.match(line)
            if match:
                name = match[1].strip()
                if name.lower().startswith('include '):
                    target = name[8:].strip()
                    prefix = config_root.rstrip('/') + '/'
                    target_path = root / target[len(prefix):] if target.startswith(prefix) else Path(target)
                    if not target_path.is_absolute():
                        target_path = path.parent / target_path
                    matches = sorted(glob.glob(str(target_path)))
                    if not matches:
                        result['unresolved'].append({'path': str(target_path), 'reason': 'include has no local matches', 'from': key, 'line': number})
                    for child in matches:
                        walk(child, stack + [resolved])
                    current = None
                    continue
                current = {'name': name, 'file': key, 'line': number, 'options': {}, 'body': []}
                canonical = name.lower()
                if canonical in sections:
                    result['duplicate_sections'].append({'section': name, 'previous': sections[canonical]['file'], 'file': key, 'line': number})
                if canonical in sections:
                    current['options'].update(sections[canonical]['options'])
                sections[canonical] = current
                continue
            if current is None:
                continue
            current['body'].append(line)
            option = OPTION.match(line)
            if option:
                current['options'][option[1].strip()] = option[2].strip()
        # Compile only actual Python files referenced with !!include. Inline
        # Kalico Python and Jinja need their target runtime, not Python compile.
        for match in re.finditer(r'!!include\s+([^\s#;]+)', '\n'.join(line for line in path.read_text(errors='replace').splitlines() if not line.lstrip().startswith(('#', ';')))):
            py = path.parent / match[1]
            if not py.resolve().is_relative_to(root) or not py.is_file():
                result['unresolved'].append({'path': str(py), 'reason': 'Python include unavailable'})
            else:
                try:
                    ast.parse(py.read_text(), filename=str(py))
                except SyntaxError as exc:
                    result['python_errors'].append({'file': str(py.relative_to(root)), 'line': exc.lineno, 'message': exc.msg})

    walk(root / entry, [])
    for current in sections.values():
        name = current['name']
        if name.lower() == 'save_variables':
            result['save_variables'].append(current['options'].get('filename'))
        if not name.lower().startswith('gcode_macro '):
            continue
        body = '\n'.join(current['body'])
        macro = name[12:].upper()
        result['macros'][macro] = {'file': current['file'], 'line': current['line'],
                                  'parameters_observed': sorted({next(x for x in m if x) for m in PARAM.findall(body)}),
                                  'language': 'kalico-python' if re.search(r'^\s*!', body, re.M) else 'jinja',
                                  'variables': sorted(k[9:] for k in current['options'] if k.startswith('variable_'))}
        for option, value in current['options'].items():
            if option.startswith('variable_'):
                # Remove config comments, as the config reader does. Complex
                # quoting/comment cases are left to the real parser.
                value = re.split(r'\s+[;#]', value, maxsplit=1)[0]
                try:
                    ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    result['literal_errors'].append({'file': current['file'], 'macro': macro, 'option': option, 'value': value})
    return result


def audit(master, repo):
    profile = json.loads((repo / 'fleet.json').read_text())
    contract = json.loads((master / 'docs/fleet/v1/baseline.json').read_text())
    report = {'printer': profile['printer'], 'role': profile['role'],
              'contract_version': profile['contract_version'], 'promotion_status': contract['promotion_status'], 'qualification': 'NOT_EVALUATED',
              'master_changes_since_baseline': [], 'source_comparison': []}
    for file, sha in contract['source_sha256'].items():
        source = master / file
        if not source.is_file() or digest(source) != sha:
            report['master_changes_since_baseline'].append(file)
        local = repo / file
        report['source_comparison'].append({'file': file, 'state': 'missing' if not local.is_file() else 'identical' if source.is_file() and digest(local) == digest(source) else 'different'})
    if profile['contract_version'] != contract['version']:
        report['contract_mismatch'] = True
    if profile.get('entrypoint') is None:
        report['scan_status'] = 'ONBOARDING_NO_MACHINE_CONFIG'
        return report
    scan_result = scan(repo, profile['entrypoint'], profile['printer_config_root'])
    report['scan'] = scan_result
    report['missing_core_macros'] = sorted(set(contract['core_macros']) - set(scan_result['macros']))
    report['scan_status'] = 'INCOMPLETE' if scan_result['unresolved'] else 'LOCAL_GRAPH_RESOLVED'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--repos', nargs='+', type=Path, required=True)
    parser.add_argument('--json', action='store_true', help='Print full machine-readable observations')
    args = parser.parse_args()
    reports = [audit(args.master.resolve(), repo.resolve()) for repo in args.repos]
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for r in reports:
            s = r.get('scan', {})
            print(f"{r['printer']}: {r['scan_status']}; qualification NOT_EVALUATED")
            print(f"  master changes: {len(r['master_changes_since_baseline'])}; unresolved: {len(s.get('unresolved', []))}; duplicate sections: {len(s.get('duplicate_sections', []))}; missing core macros: {r.get('missing_core_macros', [])}")
    # Exit 0 means the report was produced, never that the printer is safe.
    # Errors here are definite local structural findings, not drift differences.
    return int(any(r.get('contract_mismatch') or r.get('scan', {}).get('cycles') or r.get('scan', {}).get('python_errors') for r in reports))


if __name__ == '__main__':
    raise SystemExit(main())
