"""Execute the frozen outside probe; preserve every failure without retrying."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

from fep_lean.verification._subprocess import run_process_group

h=Path(__file__).resolve().parent;w=h.parent;n=w/'fep-reviewed-components-next/fep_formal';g=w/'fep119-gnn-pinned-checkout'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol_path=h/'protocol-v2.json';protocol=json.loads(protocol_path.read_text())
assert sha(protocol_path)==(h/'protocol-v2.sha256').read_text().strip()
assert sha(__file__)==protocol['capture_adapter_sha256']
assert sha(h/'validate_output.py')==protocol['checker_sha256']
spec=importlib.util.spec_from_file_location('fep61_frozen_checker',h/'validate_output.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
git=lambda root,*args:subprocess.check_output(['git',*args],cwd=root,text=True).strip()
journal=h/'execution.json';assert not journal.exists();rows=[]


def guards():
    assert sha(protocol_path)==(h/'protocol-v2.sha256').read_text().strip()
    assert sha(__file__)==protocol['capture_adapter_sha256']
    assert sha(h/'validate_output.py')==protocol['checker_sha256']
    assert sha(h/'candidate/runner.py')==protocol['runner_sha256']
    assert sha(h/'runtime_inventory_program.py.txt')==protocol['runtime_inventory_program_sha256']
    assert sha(h/'runtime-inventory.json')==protocol['runtime_inventory_sha256']
    assert git(n,'rev-parse','HEAD')==protocol['FEP_candidate_head']
    assert git(g,'rev-parse','HEAD')==protocol['GNN_head']
    assert not git(n,'status','--porcelain') and not git(g,'status','--porcelain')
    for key,root in [('fep_lean',n),('gnn',g)]:
        actual={p:sha(root/p)for p in protocol['owners'][key]}
        checker.validate_binding(actual,protocol['owners'][key])
    inventory=subprocess.check_output([str(h/'runtime/bin/python'),'-I','-B','-c',(h/'runtime_inventory_program.py.txt').read_text()])
    assert hashlib.sha256(inventory).hexdigest()==protocol['runtime_inventory_sha256']


def persist(*,complete=False,passed=False,error=None):
    data={'protocol_sha256':sha(protocol_path),'capture_adapter_sha256':sha(__file__),'FEP_candidate_head':protocol['FEP_candidate_head'],'GNN_head':protocol['GNN_head'],'checks':rows,'complete':complete,'passed':passed,'failure_reason':error,'coordinator_python':sys.version,'coordinator_executable_sha256':sha(sys.executable),'boundary':protocol['boundaries']}
    journal.write_text(json.dumps(data,indent=2)+'\n')


try:
    previous=None
    for index in range(protocol['invocations']):
        guards()
        directory=h/f'invocation-{index+1}';directory.mkdir(exist_ok=False)
        output=directory/'output';output.mkdir();home=directory/'home';home.mkdir();cache=directory/'cache';cache.mkdir()
        env=dict(protocol['environment']);env.update(GNN_OUTPUT_DIR=str(output),HOME=str(home),XDG_CACHE_HOME=str(cache),JAX_COMPILATION_CACHE_DIR=str(cache/'jax'))
        start=time.monotonic();result=run_process_group(protocol['command'],cwd=directory,env=env,timeout=protocol['deadline_seconds_per_invocation'],check=False)
        (directory/'stdout.txt').write_text(result.stdout);(directory/'stderr.txt').write_text(result.stderr)
        row={'invocation':index+1,'command':protocol['command'],'environment':env,'returncode':result.returncode,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(directory/'stdout.txt'),'stderr_sha256':sha(directory/'stderr.txt')};rows.append(row);persist()
        assert result.returncode==0 and not result.stderr,'nonzero exit or stderr'
        members=list(output.iterdir());assert len(members)==1 and members[0].name=='simulation_results.json' and not members[0].is_symlink() and members[0].is_file()
        payload=checker.strict_json(members[0].read_text());comparison=checker.validate(payload,jax_version='0.9.2')
        stable=dict(payload);del stable['execution_time_seconds'];encoded=json.dumps(stable,sort_keys=True,allow_nan=False).encode()
        if previous is not None:assert encoded==previous,'numerical replay changed'
        previous=encoded;guards()
        row.update(output_sha256=sha(members[0]),comparison=comparison,stable_payload_sha256=hashlib.sha256(encoded).hexdigest(),source_runtime_before_after_unchanged=True);persist()
    persist(complete=True,passed=True)
    print(json.dumps({'passed':True,'invocations':len(rows),'boundary':'Outside one-step initial Kalman update; no OU dynamics, native or H3 primary claim.'}))
except Exception as error:
    persist(error=type(error).__name__+': '+str(error))
    raise
