# JIDT's Java API is used instead of the GUI for two reasons:
# 1. The GUI's Theiler window counts retained rows rather than actual
#    elapsed hours. Since the wave datasets contain missing observations,
#    45 rows do not necessarily correspond to 45 hours.
# 2. The GUI cannot directly handle the two-dimensional directional
#    variable (Dx, Dy) required for directional CMI.
#
# The Java API allows exact 45-hour temporal exclusion across gaps
# and joint directional CMI estimation, while ensuring consistent
# estimator settings across both sites and all three measures.

"""Calculate six primary zero-lag estimates on actual Java exact-hour integration; no surrogate tests."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd
from autocorrelation import hourly_indices
from jidt_timing import timed_blocks
from build_jidt_official import BUILD, COMMIT, JAR, SOURCE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/primary_information'
JAVA_FILES=['ElapsedHourLoader.java','SharedEstimatorSettings.java','ExactTheilerIntegrationCheck.java','PrimaryInformationMeasures.java']
SITES=['figure_eight_pools','stockton']

#verify that files have not changed
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def run(command, log):
    r=subprocess.run(command,capture_output=True,text=True)
    log.write_text(r.stdout+r.stderr)
    r.check_returncode()
    return r


def verify_build():
    manifest=json.loads((BUILD/'build_manifest.json').read_text())
    if manifest['commit']!=COMMIT or manifest['jar_sha256']!=digest(JAR):
        raise RuntimeError('JIDT build provenance mismatch; rebuild pinned official source')
    if subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()!=COMMIT:
        raise RuntimeError('Wrong upstream commit')
    if subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip():
        raise RuntimeError('Official source modified; refusing to proceed')
    return {**manifest,'jar':str(JAR.relative_to(ROOT))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration-only',action='store_true')
    args=parser.parse_args()
    integration=OUT/'integration'; classes=integration/'classes';classes.mkdir(parents=True,exist_ok=True)
    
    #Protecting existing files
    protected=[*sorted((ROOT/'data/raw').rglob('*')),
               *sorted((ROOT/'data/processed').glob('*')),
               *sorted((ROOT/'results/preprocessing').glob('*')),
               *sorted((ROOT/'results/exploratory_figures').glob('*')),
               ROOT/'src/preprocess.py',ROOT/'src/autocorrelation.py',
               Path('/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar')]
    hashes={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):digest(p) for p in protected if p.is_file()}
    acceptance={'passed':False,'source_commit':COMMIT}
    (integration/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
    try:
        build=verify_build()
        java_version=subprocess.run(['java','-version'],capture_output=True,text=True,check=True).stderr.strip()
        cp=str(classes)+':'+str(JAR)
        run(['javac','-cp',str(JAR),'-d',str(classes),*[str(ROOT/'src/java'/f) for f in JAVA_FILES]],integration/'compile.log')
        test=run(['java','-cp',cp,'ExactTheilerIntegrationCheck',str(integration)],integration/'java.log')
        evidence=json.loads((integration/'java_results.json').read_text())
        if not evidence.get('exact_45_hour_integration_passed'): raise RuntimeError('Exact-hour integration failed: main estimates blocked')
        # Same seed/settings/data repeated solely to verify deterministic integration.
        before=(integration/'java_results.json').read_bytes()
        
        #Compile Java and test the Theiler window 
        # Running the synthetic integration test
        run(['java','-cp',cp,'ExactTheilerIntegrationCheck',str(integration)],integration/'repeat_java.log')
        if before!=(integration/'java_results.json').read_bytes(): raise RuntimeError('Seeded Java repeat differs')
        acceptance.update(passed=True,build=build,java_version=java_version,settings_readback_verified=True,
                          java_sources_sha256={f:digest(ROOT/'src/java'/f) for f in JAVA_FILES},
                          synthetic_tests=evidence,seeded_synthetic_repeat_identical=True)
        (integration/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
        if args.integration_only:
            print('PASS: exact-hour Java integration; no final estimates requested')
            return
        config=json.loads((ROOT/'results/preprocessing/theiler_window_selection.json').read_text())
        if config['common_baseline_window_hours']!=45: raise RuntimeError('Unexpected selected baseline')
        expected={r['site']:r['observations'] for r in config['sites']}
        summaries=[];tie_rows=[];site_checks=[]

        # Everything inside this loop runs separately for Figure Eight Pools and Stockton.
        for site in SITES:
            input_path=ROOT/f'data/processed/{site}.csv';data=pd.read_csv(input_path)
            if len(data)!=expected[site]: raise RuntimeError('Sample count differs from ACF dataset')
            hours=hourly_indices(data.timestamp_utc);blocks=list(timed_blocks(data.timestamp_utc))
            
            # Validate the required variables
            columns=['Ho','Hn','Tp_o','Dx','Dy']
            if not np.isfinite(data[columns].to_numpy()).all():raise RuntimeError('Nonfinite inputs; do not silently filter')
            if not (data[['Ho','Hn']].ge(0).all().all() and data.Tp_o.gt(0).all()):raise RuntimeError('Invalid measurements')
            if not data.Qflag.eq(1).all() or not data.WAVE_quality_control.eq(1).all():raise RuntimeError('Unexpected QC flag')
            if not np.allclose(data.Dx**2+data.Dy**2,1):raise RuntimeError('Direction components invalid')
            for label,cols in [('Ho',['Ho']),('Hn',['Hn']),('Tp_o',['Tp_o']),('direction',['Dx','Dy']),('height_pair',['Ho','Hn']),('all_variables',columns)]:
                tie_rows.append({'site':site,'variable_or_tuple':label,'observations':len(data),
                                 'distinct_values_or_tuples':len(data[cols].drop_duplicates()),
                                 'rows_in_repeated_groups':int(data.duplicated(cols,keep=False).sum()),
                                 'duplicate_rows_beyond_first':int(data.duplicated(cols).sum())})
            # Raw measurement values, no external normalization/noise or filled hours.

            # Create the Java input file
            prepared=OUT/f'{site}_java_input.csv'
            with prepared.open('w') as f:
                for h,row in zip(hours,data[columns].to_numpy()):f.write(str(int(h))+','+','.join(format(v,'.17g') for v in row)+'\n')
            pd.DataFrame(blocks,columns=['row_start','row_stop','elapsed_hour_start']).to_csv(OUT/f'{site}_segments.csv',index=False)

            # Calculate the three information measures
            result=OUT/f'{site}_estimates.csv';times=OUT/f'{site}_java_indices.csv'
            run(['java','-cp',cp,'PrimaryInformationMeasures',str(prepared),str(result),str(times)],OUT/f'{site}.log')
            
            #Verify that Java received the correct timestamps
            actual=pd.read_csv(times)
            for col in ['expected_elapsed_hour','mi_time','period_time','direction_time']:
                np.testing.assert_array_equal(actual[col],hours)
            for col in ['mi_set','period_set','direction_set']:
                np.testing.assert_array_equal(actual[col],np.zeros(len(data),dtype=int))
            
            # Verify and organise the MI/CMI results
            estimates=pd.read_csv(result)
            assert len(estimates)==3 and estimates.sample_size.eq(len(data)).all()
            np.testing.assert_allclose(estimates.bits,estimates.nats/np.log(2),rtol=1e-14)
            estimates['site']=site
            estimates['measure']=estimates.measure.replace({'I((Dx Dy);Hn|Ho)':'I((Dx,Dy);Hn|Ho)'})
            estimates['algorithm']='Kraskov algorithm 1'
            estimates['java_version']=java_version.splitlines()[0]
            estimates['jidt_version']='1.6.1 official-source snapshot'
            estimates['jidt_commit']=COMMIT;estimates['jidt_jar_sha256']=digest(JAR)
            estimates['noise_stage']='JIDT Gaussian after normalization'
            estimates['exclusion_units']='exact elapsed hours';estimates['lag_hours']=0
            estimates['source_csv_sha256']=digest(input_path)
            estimates['first_timestamp_utc']=data.timestamp_utc.iloc[0]
            estimates['last_timestamp_utc']=data.timestamp_utc.iloc[-1]
            estimates['timestamp_sequence_sha256']=hashlib.sha256('\n'.join(data.timestamp_utc).encode()).hexdigest()
            estimates['calculator_class']=[
                'infodynamics.measures.continuous.kraskov.MutualInfoCalculatorMultiVariateKraskov1',
                'infodynamics.measures.continuous.kraskov.ConditionalMutualInfoCalculatorMultiVariateKraskov1',
                'infodynamics.measures.continuous.kraskov.ConditionalMutualInfoCalculatorMultiVariateKraskov1']
            summaries.append(estimates)
            pd.DataFrame({'timestamp_utc':data.timestamp_utc,'elapsed_hour_index':hours}).to_csv(OUT/f'{site}_retained_timestamps.csv',index=False)
            site_checks.append({'site':site,'observations':len(data),'segments':len(blocks),
                                'all_Java_time_indices_match':True,'all_Java_set_ids_zero':True,'no_rows_removed':True})
        
        # Combine and save the final results
        summary=pd.concat(summaries,ignore_index=True)
        first=['site','measure','sample_size','x_dimensions','y_dimensions','condition_dimensions']
        summary=summary[first+[c for c in summary if c not in first]]
        summary.to_csv(OUT/'primary_information_summary.csv',index=False)
        pd.DataFrame(tie_rows).to_csv(OUT/'ties_audit.csv',index=False)
        (OUT/'site_loading_checks.json').write_text(json.dumps(site_checks,indent=2)+'\n')
        print(summary[['site','measure','sample_size','nats','bits']].to_string(index=False))
    
    # The finally block executes whether the main calculation succeeds or fails.
    finally:
        unchanged=all(digest(Path(p) if Path(p).is_absolute() else ROOT/p)==sha for p,sha in hashes.items())
        protection={'protected_files_unchanged':unchanged,'sha256':hashes}
        (OUT/'preservation_checks.json').write_text(json.dumps(protection,indent=2)+'\n')
        if not unchanged:raise RuntimeError('Protected file changed')


if __name__=='__main__':main()
