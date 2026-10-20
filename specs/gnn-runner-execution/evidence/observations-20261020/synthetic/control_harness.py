"""Physical refusal controls for the unchanged historical capture adapter.

Synthetic fixture Git repositories/runtime and saved numerical output only.
This is not another generated-runner observation or Issue61 acceptance.
Execute only under the owning FEP operation lease.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

W = Path(__file__).resolve().parent
ORIGINAL = W / 'fep61-runtime-proposal'
DEST = W / 'fep61-capture-adapter-controls-v1'
ADAPTER = (ORIGINAL / 'capture.py').read_bytes()
CHECKER = (ORIGINAL / 'validate_output.py').read_bytes()
PAYLOAD = json.loads((ORIGINAL / 'invocation-1/output/simulation_results.json').read_text())
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
CASES = ['positive', 'missing-output', 'malformed-output', 'extra-output',
         'symlink-output', 'nonzero', 'stderr', 'deadline', 'missing-runner',
         'replacement-runner', 'replacement-checker', 'replacement-protocol',
         'stale-source-head', 'missing-owner', 'wrong-owner-digest',
         'replacement-runtime-inventory', 'replacement-runtime-program',
         'runtime-observation-mismatch', 'post-run-owner-replacement',
         'second-output-mismatch', 'preexisting-journal', 'preexisting-invocation']
assert not DEST.exists()
DEST.mkdir()
rows = []

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()

for case in CASES:
    layout = DEST / case
    h = layout / 'fep61-runtime-proposal'
    n = layout / 'fep-reviewed-components-next/fep_formal'
    g = layout / 'fep119-gnn-pinned-checkout'
    for root in [n, g]:
        root.mkdir(parents=True)
        git(root, 'init', '-q')
        git(root, 'config', 'user.name', 'Synthetic capture control')
        git(root, 'config', 'user.email', 'capture-control@example.invalid')
        (root / 'owner.txt').write_text('synthetic owner\n')
        git(root, 'add', 'owner.txt')
        git(root, 'commit', '-qm', 'Synthetic fixture only')
    h.mkdir(parents=True)
    (h / 'candidate').mkdir()
    (h / 'capture.py').write_bytes(ADAPTER)
    (h / 'validate_output.py').write_bytes(CHECKER)
    (h / 'runtime/bin').mkdir(parents=True)
    (h / 'runtime/bin/python').symlink_to(sys.executable)
    # A deliberately small physical fixture runtime inventory, not the 3270-member runtime.
    marker = h / 'runtime/marker.txt'
    marker.write_text('synthetic runtime marker\n')
    inventory_code = ('from pathlib import Path; import hashlib,json; '
                      f'p=Path({str(marker)!r}); '
                      'print(json.dumps({"fixture_runtime_marker_sha256":hashlib.sha256(p.read_bytes()).hexdigest()},sort_keys=True))')
    (h / 'runtime_inventory_program.py.txt').write_text(inventory_code)
    inventory = subprocess.check_output([str(h / 'runtime/bin/python'), '-I', '-B', '-c', inventory_code])
    (h / 'runtime-inventory.json').write_bytes(inventory)
    payload = dict(PAYLOAD)
    payload['execution_time_seconds'] = 0.01
    runner = ['import json,os,sys,time', 'from pathlib import Path',
              'out=Path(os.environ["GNN_OUTPUT_DIR"])', f'p={payload!r}']
    if case == 'deadline':
        runner.append('time.sleep(30)')
    elif case == 'nonzero':
        runner.append('sys.exit(7)')
    elif case == 'missing-output':
        pass
    elif case == 'malformed-output':
        runner.append('(out/"simulation_results.json").write_text("{broken")')
    elif case == 'symlink-output':
        runner.extend(['other=out.parent/"outside.json"', 'other.write_text(json.dumps(p))',
                       '(out/"simulation_results.json").symlink_to(other)'])
    else:
        if case == 'second-output-mismatch':
            runner.extend(['if Path.cwd().name=="invocation-2":', ' p["observations_continuous"][0][0]+=1.0', ' p["beliefs"][0][0]+=0.5', ' p["rmse_vs_true"]=abs(p["beliefs"][0][0]-p["true_states_continuous"][0][0])'])
        runner.append('(out/"simulation_results.json").write_text(json.dumps(p))')
        if case == 'extra-output':
            runner.append('(out/"extra.txt").write_text("unexpected")')
        elif case == 'stderr':
            runner.append('print("controlled diagnostic",file=sys.stderr)')
        elif case == 'post-run-owner-replacement':
            runner.append(f'Path({str(n / "owner.txt")!r}).write_text("replaced after execution")')
    (h / 'candidate/runner.py').write_text('\n'.join(runner) + '\n')
    owners = {'fep_lean': {'owner.txt': SHA(n / 'owner.txt')}, 'gnn': {'owner.txt': SHA(g / 'owner.txt')}}
    protocol = {'capture_adapter_sha256': SHA(h / 'capture.py'), 'checker_sha256': SHA(h / 'validate_output.py'),
                'runner_sha256': SHA(h / 'candidate/runner.py'),
                'runtime_inventory_program_sha256': SHA(h / 'runtime_inventory_program.py.txt'),
                'runtime_inventory_sha256': SHA(h / 'runtime-inventory.json'),
                'FEP_candidate_head': git(n, 'rev-parse', 'HEAD'), 'GNN_head': git(g, 'rev-parse', 'HEAD'),
                'owners': owners, 'invocations': 2, 'deadline_seconds_per_invocation': 0.3 if case == 'deadline' else 10,
                'environment': {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'},
                'command': [str(h / 'runtime/bin/python'), '-I', '-B', str(h / 'candidate/runner.py')],
                'boundaries': ['Synthetic physical capture-adapter control only; fixture output replay is not a scientific runner observation.',
                               'Two one-file synthetic Git owners and one-marker fixture runtime; no 3270-member runtime replacement claim.']}
    if case == 'stale-source-head': protocol['FEP_candidate_head'] = '0' * 40
    if case == 'missing-owner': protocol['owners']['fep_lean']['absent.txt'] = '0' * 64
    if case == 'wrong-owner-digest': protocol['owners']['fep_lean']['owner.txt'] = '0' * 64
    if case == 'runtime-observation-mismatch':
        (h / 'runtime-inventory.json').write_text('{"different_observation":true}\n')
        protocol['runtime_inventory_sha256'] = SHA(h / 'runtime-inventory.json')
    (h / 'protocol-v2.json').write_text(json.dumps(protocol, indent=2) + '\n')
    frozen = SHA(h / 'protocol-v2.json')
    (h / 'protocol-v2.sha256').write_text(frozen + '\n')
    shutil.copy2(h / 'protocol-v2.json', layout / 'protocol-before-injected-control.json')
    mutations = {'replacement-runner': 'candidate/runner.py', 'replacement-checker': 'validate_output.py',
                 'replacement-protocol': 'protocol-v2.json', 'replacement-runtime-inventory': 'runtime-inventory.json',
                 'replacement-runtime-program': 'runtime_inventory_program.py.txt'}
    if case in mutations:
        target = h / mutations[case]
        target.write_bytes(target.read_bytes() + (b'\n ' if case == 'replacement-protocol' else b'\n# controlled replacement\n'))
    if case == 'missing-runner': (h / 'candidate/runner.py').unlink()
    if case == 'preexisting-journal': (h / 'execution.json').write_text('{"existing":"preserve"}\n')
    if case == 'preexisting-invocation': (h / 'invocation-1').mkdir()
    original_journal = (h / 'execution.json').read_bytes() if (h / 'execution.json').exists() else None
    start = time.monotonic()
    result = subprocess.run([sys.executable, '-B', str(h / 'capture.py')], cwd=layout,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                            capture_output=True, timeout=30)
    (layout / 'stdout.bin').write_bytes(result.stdout)
    (layout / 'stderr.bin').write_bytes(result.stderr)
    journal = json.loads((h / 'execution.json').read_text()) if (h / 'execution.json').is_file() else None
    passed = (result.returncode == 0 and journal and journal.get('complete') and journal.get('passed')) if case == 'positive' else result.returncode != 0 and (not journal or not journal.get('passed'))
    if original_journal is not None: passed = passed and (h / 'execution.json').read_bytes() == original_journal
    if case == 'deadline': passed = passed and journal is not None and 'Timeout' in journal.get('failure_reason', '')
    if case == 'post-run-owner-replacement': passed = passed and journal is not None and len(journal['checks']) == 1
    # Every negative must reach its intended branch, not merely exit nonzero.
    expected_rows = 2 if case in ['positive', 'second-output-mismatch'] else 1 if case in ['missing-output', 'malformed-output', 'extra-output', 'symlink-output', 'nonzero', 'stderr', 'post-run-owner-replacement'] else 0
    expected_dirs = expected_rows if expected_rows else 1 if case in ['deadline', 'preexisting-invocation'] else 0
    invocation_dirs = sorted(h.glob('invocation-*'))
    passed = passed and len(invocation_dirs) == expected_dirs
    top_guard = case in ['replacement-checker', 'replacement-protocol', 'preexisting-journal']
    if top_guard:
        passed = passed and ((journal is None) if case != 'preexisting-journal' else journal == {'existing': 'preserve'})
    else:
        passed = passed and journal is not None and len(journal['checks']) == expected_rows
    markers = {
        'missing-output': 'assert len(members)==1', 'malformed-output': 'json.decoder.JSONDecodeError:',
        'extra-output': 'assert len(members)==1', 'symlink-output': 'assert len(members)==1',
        'nonzero': 'AssertionError: nonzero exit or stderr', 'stderr': 'AssertionError: nonzero exit or stderr',
        'deadline': 'result=run_process_group(', 'missing-runner': 'candidate/runner.py',
        'replacement-runner': "assert sha(h/'candidate/runner.py')", 'replacement-checker': "assert sha(h/'validate_output.py')",
        'replacement-protocol': 'assert sha(protocol_path)', 'stale-source-head': "assert git(n,'rev-parse','HEAD')",
        'missing-owner': 'absent.txt', 'wrong-owner-digest': 'ValueError: missing, stale or replaced source/runtime binding',
        'replacement-runtime-inventory': "assert sha(h/'runtime-inventory.json')",
        'replacement-runtime-program': "assert sha(h/'runtime_inventory_program.py.txt')",
        'runtime-observation-mismatch': 'assert hashlib.sha256(inventory)',
        'post-run-owner-replacement': "assert not git(n,'status','--porcelain')",
        'second-output-mismatch': 'AssertionError: numerical replay changed',
        'preexisting-journal': 'assert not journal.exists()', 'preexisting-invocation': 'FileExistsError:',
    }
    expected_marker = markers.get(case)
    if expected_marker: passed = passed and expected_marker in result.stderr.decode(errors='replace')
    outputs = sorted((h / 'invocation-1/output').iterdir()) if (h / 'invocation-1/output').is_dir() else []
    if case == 'missing-output': passed = passed and not outputs
    if case == 'extra-output': passed = passed and {p.name for p in outputs} == {'simulation_results.json', 'extra.txt'}
    if case == 'symlink-output': passed = passed and len(outputs) == 1 and outputs[0].is_symlink()
    if case == 'malformed-output': passed = passed and (h / 'invocation-1/output/simulation_results.json').read_text() == '{broken'
    if case == 'nonzero': passed = passed and journal['checks'][0]['returncode'] == 7
    if case == 'stderr': passed = passed and (h / 'invocation-1/stderr.txt').read_text() == 'controlled diagnostic\n'
    if case == 'deadline': passed = passed and not (h / 'invocation-1/stdout.txt').exists()
    if case == 'post-run-owner-replacement': passed = passed and (n / 'owner.txt').read_text() == 'replaced after execution'
    if case == 'preexisting-invocation': passed = passed and not (h / 'invocation-1/output').exists()
    rows.append({'case': case, 'passed': bool(passed), 'returncode': result.returncode,
                 'seconds': time.monotonic() - start, 'expected_failure_marker': expected_marker, 'expected_captured_rows': expected_rows, 'expected_invocation_directories': expected_dirs, 'protocol_before_mutation_sha256': frozen,
                 'adapter_sha256': SHA(h / 'capture.py'), 'stdout_sha256': SHA(layout / 'stdout.bin'),
                 'stderr_sha256': SHA(layout / 'stderr.bin'), 'journal': journal,
                 'original_journal_preserved': original_journal is None or (h / 'execution.json').read_bytes() == original_journal})
    (DEST / 'qualification.json').write_text(json.dumps({'script_sha256': SHA(__file__), 'adapter_sha256': hashlib.sha256(ADAPTER).hexdigest(),
        'complete': len(rows) == len(CASES), 'passed': all(r['passed'] for r in rows), 'checks': rows,
        'boundary': 'Actual unchanged adapter exercised against synthetic physical fixture sources/runtime and saved payload. No new generated-runner, OU dynamics, native or full Issue61 acceptance.'}, indent=2) + '\n')
    print(case, 'PASS' if passed else 'FAIL', flush=True)
    assert passed, rows[-1]
