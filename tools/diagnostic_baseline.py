"""Protect HW2 and imported diagnostic archives; write rebuilds separately."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HW2_BASE = 'df52834b94a69f3c4909b6748974b20f6e77f598'
MANIFEST = 'docs/diagnostic_consolidation/sources.json'

def verify_archives(root=ROOT):
    root = Path(root).resolve()
    records = json.loads((root / MANIFEST).read_text(encoding='utf-8'))['files']
    records = [r for r in records if r['path'].startswith(('docs/', 'releases/'))]
    if not records:
        return 0
    paths = [r['path'] for r in records]
    # Git applies checkout filters here, so CRLF checkouts compare to original blobs.
    result = subprocess.run(['git', 'hash-object', '--stdin-paths'], cwd=root,
        input='\n'.join(paths)+'\n', text=True, capture_output=True, check=True)
    hashes = result.stdout.splitlines()
    if len(hashes) != len(records):
        raise ValueError('Incomplete archive hash verification')
    changed = [r['path'] for r,h in zip(records,hashes) if h != r['blob_sha']]
    if changed:
        raise ValueError('Archived diagnostic evidence changed: '+', '.join(changed))
    return len(records)

def protect(output, root=ROOT, baseline=HW2_BASE):
    root, output = Path(root).resolve(), Path(output).resolve()
    if root.is_relative_to(output) or (output.is_relative_to(root) and
                                      not output.is_relative_to(root/'build')):
        raise ValueError('Diagnostic output must be under build/ or outside the repository')
    # This is a main ancestor, never an otherwise unreachable topic-branch commit.
    if subprocess.run(['git', 'merge-base', '--is-ancestor', baseline, 'HEAD'],
                      cwd=root, capture_output=True).returncode:
        raise ValueError('HW2 baseline is missing/not an ancestor; use a full main checkout')
    paths = ['src', 'assets', 'releases', 'tools', 'AGENTS.md']
    old = set(subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', baseline,
                                      '--', *paths], cwd=root, text=True).splitlines())
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', baseline,
                                          '--', *paths], cwd=root, text=True).splitlines())
    protected = sorted(old & changed)
    if protected:
        raise ValueError('Protected HW2 baseline changed: '+', '.join(protected))
    verify_archives(root)
    return output
