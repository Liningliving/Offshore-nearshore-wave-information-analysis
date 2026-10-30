"""Focused installed-JIDT check. Exit 1 means the exact-hour acceptance criterion failed."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/results/theiler_integration'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar',type=Path,default=Path('/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar'))
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    protected=[*sorted((ROOT/'outputs/cleaned').glob('*.csv')),
               ROOT/'outputs/results/autocorrelation_decay_summary.csv',
               ROOT/'outputs/results/theiler_window_selection.json']
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    evidence={'jar':str(args.jar),'python_to_java':'subprocess; no JPype bridge required',
              'jpype_installed':importlib.util.find_spec('jpype') is not None}
    try:
        evidence['java_version']=subprocess.run(['java','-version'],capture_output=True,text=True,check=True).stderr
        evidence['jar_sha256']=hashlib.sha256(args.jar.read_bytes()).hexdigest()
        compile_run=subprocess.run(['javac','-cp',str(args.jar),'-d',str(OUT),str(ROOT/'src/java/TheilerIntegrationCheck.java')],capture_output=True,text=True,check=True)
        command=['java','-cp',str(OUT)+':'+str(args.jar),'TheilerIntegrationCheck',str(OUT)]
        run=subprocess.run(command,capture_output=True,text=True)
        (OUT/'java_execution.log').write_text(run.stdout+run.stderr)
        run.check_returncode()
        result=json.loads((OUT/'java_results.json').read_text())
        evidence.update(command=command,returncode=run.returncode,java_test_executed=True,
                        exact_45_hour_integration_passed=result['exact_45_hour_integration_passed'])
        print(run.stdout)
    except (OSError,subprocess.CalledProcessError) as error:
        evidence.update(java_test_executed=False,error=str(error))
        if isinstance(error,subprocess.CalledProcessError): evidence['error_output']=(error.stdout or '')+(error.stderr or '')
    unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in before.items())
    evidence.update(protected_file_sha256=before,protected_files_unchanged=unchanged)
    (OUT/'python_execution.json').write_text(json.dumps(evidence,indent=2)+'\n')
    if not unchanged: raise RuntimeError('Protected files changed unexpectedly')
    accepted=evidence.get('exact_45_hour_integration_passed',False)
    print('Exact 45-hour integration: '+('PASS' if accepted else 'FAIL (see evidence; do not proceed as an exact-hour analysis)'))
    return 0 if accepted else 1


if __name__=='__main__': sys.exit(main())
