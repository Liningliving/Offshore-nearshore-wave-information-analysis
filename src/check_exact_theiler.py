"""Verify the pinned official JIDT runtime, exact time loading and both site mappings."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np
from build_jidt_official import COMMIT, JAR, BUILD, SOURCE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/results/theiler_exact_integration'
JAVA_FILES=['ElapsedHourLoader.java','WaveInformationExact.java','ExactTheilerIntegrationCheck.java','CheckSiteTiming.java']


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def verified_build():
    manifest=json.loads((BUILD/'build_manifest.json').read_text())
    if manifest['commit']!=COMMIT or digest(JAR)!=manifest['jar_sha256']:
        raise RuntimeError('Pinned build manifest/jar mismatch')
    if subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()!=COMMIT:
        raise RuntimeError('Official source commit changed')
    if subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip():
        raise RuntimeError('Official estimator source modified')
    return manifest


def require_exact_gate(jar=JAR):
    gate=json.loads((OUT/'acceptance.json').read_text())
    if not gate.get('accepted') or gate['commit']!=COMMIT or digest(jar)!=gate['jar_sha256']:
        raise RuntimeError('Exact-time runtime acceptance is absent or stale; run src/check_exact_theiler.py')
    for name,sha in gate['java_sources_sha256'].items():
        if digest(ROOT/'src/java'/name)!=sha: raise RuntimeError('Java adapter changed; repeat focused integration check')
    return gate


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files=[*sorted((ROOT/'outputs/cleaned').glob('*.csv')),
           *sorted((ROOT/'outputs/results').glob('*autocorrelation*')),
           *sorted((ROOT/'outputs/figures').glob('*autocorrelation*')),
           ROOT/'outputs/results/theiler_window_selection.json',
           ROOT/'outputs/results/information_results.csv',ROOT/'outputs/results/information_settings.json',
           Path('/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar')]
    before={str(p):digest(p) for p in files if p.is_file()}
    gate={'accepted':False,'commit':COMMIT,'protected_files_sha256':before}
    (OUT/'acceptance.json').write_text(json.dumps(gate,indent=2)+'\n')
    try:
        manifest=verified_build();classes=OUT/'classes';classes.mkdir(exist_ok=True)
        sources=[str(ROOT/'src/java'/name) for name in JAVA_FILES]
        result=subprocess.run(['javac','-cp',str(JAR),'-d',str(classes),*sources],capture_output=True,text=True)
        (OUT/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
        cp=str(classes)+':'+str(JAR)
        test=subprocess.run(['java','-cp',cp,'ExactTheilerIntegrationCheck',str(OUT)],capture_output=True,text=True)
        (OUT/'java_execution.log').write_text(test.stdout+test.stderr);test.check_returncode()
        evidence=json.loads((OUT/'java_results.json').read_text())
        if not evidence['exact_45_hour_integration_passed']: raise RuntimeError('Exact-hour runtime check failed')
        sites={}
        for site in ['figure_eight_pools','stockton']:
            r=subprocess.run(['java','-cp',cp,'CheckSiteTiming',str(ROOT/f'outputs/cleaned/{site}.csv')],capture_output=True,text=True,check=True)
            sites[site]=json.loads(r.stdout)
        (OUT/'site_metadata_checks.json').write_text(json.dumps(sites,indent=2)+'\n')
        # End-to-end application runner smoke test: synthetic data only.
        rng=np.random.default_rng(20261030)
        hours=np.r_[np.arange(80),np.arange(90,170),np.arange(240,320),400]
        data=rng.normal(size=(len(hours),5));theta=rng.uniform(0,2*np.pi,len(hours));data[:,3]=np.cos(theta);data[:,4]=np.sin(theta)
        np.savetxt(OUT/'synthetic_input.csv',data,delimiter=',',fmt='%.17g');np.savetxt(OUT/'synthetic_hours.csv',hours,fmt='%d')
        smoke={}
        for measure in ['mi_height','cmi_period','cmi_direction']:
            output=OUT/f'{measure}_smoke.csv'
            r=subprocess.run(['java','-cp',cp,'WaveInformationExact',str(OUT/'synthetic_input.csv'),str(output),measure,'4','45','3','0' if measure=='mi_height' else '10','20261030',str(OUT/'synthetic_hours.csv')],capture_output=True,text=True,check=True)
            audit=json.loads(Path(str(output)+'.timing.json').read_text())
            if not (audit['observations']==241 and audit['surrogate_timing_reload_checks']==3 and audit['window_hours']==45 and audit['k']==4): raise RuntimeError('End-to-end runner settings/count mismatch')
            smoke[measure]=audit
        if any(digest(Path(p))!=sha for p,sha in before.items()): raise RuntimeError('Protected input/results changed')
        gate.update(accepted=True,jar_sha256=manifest['jar_sha256'],build_manifest=manifest,
                    java_sources_sha256={name:digest(ROOT/'src/java'/name) for name in JAVA_FILES},
                    runtime_results=evidence,site_checks=sites,application_runner_smoke_tests=smoke,
                    protected_files_unchanged=True,main_analysis_rerun=False)
        print(json.dumps({'accepted':True,'commit':COMMIT,'tests':evidence,'site_checks':sites},indent=2))
    except Exception as error:
        gate.update(accepted=False,error=str(error));raise
    finally:
        (OUT/'acceptance.json').write_text(json.dumps(gate,indent=2)+'\n')
    return 0


if __name__=='__main__': sys.exit(main())
