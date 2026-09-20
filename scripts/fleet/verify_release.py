#!/usr/bin/env python3
"""Run master source regressions + syntax checks + fleet inventory. Never deploys.
Exit 0 is static success only; firmware/restart/physical qualification remain separate.
Usage: python scripts/fleet/verify_release.py [--json-output /tmp/evidence.json]
Requires Jinja2 (same dependency as Klipper); Python 3.9+.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import jinja2
from check import audit

ROOT = Path(__file__).resolve().parents[2]

def templates():
    result = []
    for path in sorted((ROOT / 'custom/macros').rglob('*.cfg')):
        cfg = configparser.RawConfigParser(strict=False, inline_comment_prefixes=('#', ';'))
        cfg.read(path)
        for section in cfg.sections():
            if not cfg.has_option(section, 'gcode'):
                continue
            body = cfg.get(section, 'gcode').strip()
            label = '%s:%s' % (path.relative_to(ROOT), section)
            if body.startswith('!!include '):
                source = (path.parent / body.split(maxsplit=1)[1]).resolve()
                if not source.is_relative_to(ROOT):
                    raise ValueError('External Python include: ' + label)
                result.append(dict(name=label, language='python', source=source.read_text()))
            elif body.startswith('!'):
                source = '\n'.join(line.lstrip()[1:] for line in body.splitlines())
                result.append(dict(name=label, language='python', source=source))
            else:
                result.append(dict(name=label, language='jinja', source=body))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args()
    test_result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'scripts/fleet'), '-p', 'test_*.py'])
    env = jinja2.Environment('{%', '%}', '{', '}', extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols'])
    sources = templates()
    for template in sources:
        if template['language'] == 'python':
            compile(template['source'], template['name'], 'exec')
        else:
            env.from_string(template['source'])
    reports = [audit(ROOT, path) for path in (ROOT, ROOT.parent/'K3D', ROOT.parent/'rat-race', ROOT.parent/'mini-trip')]
    structure_errors = any(r.get('contract_mismatch') or r.get('scan',{}).get('cycles') or r.get('scan',{}).get('python_errors') for r in reports)
    success = test_result.returncode == 0 and not structure_errors
    files = [ROOT/'printer.cfg', ROOT/'mmu/base/mmu_macro_vars.cfg']
    files += sorted(p for p in (ROOT/'custom/macros').rglob('*') if p.is_file() and p.suffix in ('.cfg','.py'))
    evidence = {'static_result': 'PASS' if success else 'FAIL', 'qualification': 'NOT_QUALIFIED_FOR_DEPLOYMENT',
                'template_count': len(sources), 'jinja_version': jinja2.__version__,
                'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                'fleet': reports}
    if args.json_output:
        args.json_output.write_text(json.dumps(evidence, indent=2)+'\n')
    print('%s: %d templates compiled; fleet inventoried. NOT QUALIFIED FOR DEPLOYMENT.' % (evidence['static_result'], len(sources)))
    return int(not success)

if __name__ == '__main__':
    raise SystemExit(main())
