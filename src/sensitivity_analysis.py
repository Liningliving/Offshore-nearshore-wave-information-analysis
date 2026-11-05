"""One-factor k, physical-lag and exact-Theiler sensitivities; no significance tests."""
from pathlib import Path
import json
import hashlib
import subprocess
import numpy as np
import pandas as pd
from preprocess import PAIRS, DATA, numeric
from autocorrelation import hourly_indices
from primary_information import verify_build,digest

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/sensitivity_analysis'
LAGS=(0,.5,1,2)
COLS=['Ho','Hn','Tp_o','Dx','Dy']
MEASURES={'height_mi':'I(Ho;Hn)','period_cmi':'I(Tp_o;Hn|Ho)','direction_cmi':'I((Dx,Dy);Hn|Ho)'}


def match_frames(off,near,lag):
    """Retain offshore t; exact join with nearshore target t+lag, never row shifts."""
    delay=pd.Timedelta(hours=lag)
    left=off.copy();right=near.copy()
    left['near_timestamp_utc']=left.timestamp_utc+delay
    matched=left.merge(right,on='near_timestamp_utc',how='inner',validate='one_to_one')
    matched=matched.dropna(subset=COLS).sort_values('timestamp_utc').reset_index(drop=True)
    if not (matched.near_timestamp_utc-matched.timestamp_utc).eq(delay).all():raise ValueError('Incorrect lag matching')
    if not np.isfinite(matched[COLS].to_numpy()).all():raise ValueError('Nonfinite input; no silent filtering')
    if not (matched[['Ho','Hn']].ge(0).all().all() and matched.Tp_o.gt(0).all()):raise ValueError('Invalid values')
    hourly_indices(matched.timestamp_utc)
    return matched


def load_lags(site):
    token,station,filename=PAIRS[site]
    near_path,=DATA.glob(f'*{token}*/*Parameters.csv')
    near=pd.read_csv(near_path);off=pd.read_csv(DATA/filename,comment='#')
    if set(off.site_name)!={station}:raise ValueError('Unexpected offshore station')
    numeric(near,['Hsig','Qflag']);numeric(off,['WHTH','WPPE','WPDI','WAVE_quality_control'])
    near['near_timestamp_utc']=pd.to_datetime(near.Time,format='%d-%b-%Y %H:%M:%S').dt.tz_localize('Etc/GMT-10').dt.tz_convert('UTC')
    off['timestamp_utc']=pd.to_datetime(off.TIME,utc=True)
    if near.near_timestamp_utc.duplicated().any() or off.timestamp_utc.duplicated().any():raise ValueError('Duplicate source timestamps')
    near=near.loc[near.Qflag.eq(1),['near_timestamp_utc','Hsig']].rename(columns={'Hsig':'Hn'})
    off=off.loc[off.WAVE_quality_control.eq(1),['timestamp_utc','WHTH','WPPE','WPDI']].rename(columns={'WHTH':'Ho','WPPE':'Tp_o'})
    theta=np.deg2rad(off.WPDI);off['Dx']=np.cos(theta);off['Dy']=np.sin(theta)
    off=off[['timestamp_utc','Ho','Tp_o','Dx','Dy']]
    return {lag:match_frames(off,near,lag) for lag in LAGS}


def main():
    OUT.mkdir(parents=True,exist_ok=True);validation=OUT/'validation';validation.mkdir(exist_ok=True)
    protected=[p for directory in ['data/raw','data/processed','results/preprocessing','results/exploratory_figures','results/primary_information','research/surrogate_validation'] for p in (ROOT/directory).rglob('*') if p.is_file()]
    protected += [ROOT/'src/preprocess.py',ROOT/'src/autocorrelation.py',ROOT/'src/jidt_timing.py',ROOT/'src/primary_information.py']
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    gate={'passed':False,'reason':'Preflight not completed'}
    (validation/'acceptance.json').write_text(json.dumps(gate,indent=2)+'\n')
    try:
        build=verify_build();jar=ROOT/build['jar'];classes=validation/'classes';classes.mkdir(exist_ok=True)
        java=['ElapsedHourLoader.java','SharedEstimatorSettings.java','SensitivitySettings.java','SensitivityMeasures.java','SensitivityIntegrationCheck.java']
        process=subprocess.run(['javac','-cp',str(jar),'-d',str(classes),*[str(ROOT/'src/java'/f) for f in java]],capture_output=True,text=True)
        (validation/'compile.log').write_text(process.stdout+process.stderr);process.check_returncode()
        cp=str(classes)+':'+str(jar)
        process=subprocess.run(['java','-cp',cp,'SensitivityIntegrationCheck',str(validation/'java_integration.csv')],capture_output=True,text=True)
        (validation/'java.log').write_text(process.stdout+process.stderr);process.check_returncode()
        integration=pd.read_csv(validation/'java_integration.csv')
        assert len(integration)==12 and integration[['mi_pass','period_cmi_pass','direction_cmi_pass','boundary_and_gap_masks_pass']].all().all()
        inputs=OUT/'inputs';runs=OUT/'runs';inputs.mkdir(exist_ok=True);runs.mkdir(exist_ok=True)
        prepared={};cache={}
        def estimate(site,data,key,k=4,window=45):
            identity=(site,key,k,window)
            if identity in cache:return cache[identity].copy()
            if (site,key) not in prepared:
                hours=hourly_indices(data.timestamp_utc)
                path=inputs/f'{site}_{key}.csv'
                with path.open('w') as f:
                    for t,row in zip(hours,data[COLS].to_numpy()):f.write(str(int(t))+','+','.join(format(v,'.17g') for v in row)+'\n')
                data[['timestamp_utc','near_timestamp_utc']].to_csv(inputs/f'{site}_{key}_timestamps.csv',index=False)
                prepared[(site,key)]=(path,hours)
            path,hours=prepared[(site,key)]
            output=runs/f'{site}_{key}_k{k}_w{window}.csv';timing=runs/f'{site}_{key}_k{k}_w{window}_indices.csv'
            process=subprocess.run(['java','-cp',cp,'SensitivityMeasures',str(path),str(output),str(timing),str(k),str(window),'1.0'],capture_output=True,text=True)
            (runs/f'{site}_{key}_k{k}_w{window}.log').write_text(process.stdout+process.stderr);process.check_returncode()
            actual=pd.read_csv(timing)
            for col in ['expected_tick','mi_tick','period_tick','direction_tick']:np.testing.assert_array_equal(actual[col],hours)
            for col in ['mi_set','period_set','direction_set']:assert actual[col].eq(0).all()
            result=pd.read_csv(output,float_precision="round_trip");assert len(result)==3 and result.sample_size.eq(len(data)).all()
            np.testing.assert_allclose(result.bits,result.nats/np.log(2),rtol=1e-13,atol=1e-15)
            result['site']=site;result['measure_name']=result.measure.map(MEASURES)
            result['NORMALISE']=True;result['NORM_TYPE']='MAX_NORM';result['USE_GPU']=False
            result['noise_std']=1e-8;result['noise_seed']=20261031;result['threads']=1
            result['jidt_commit']=build['commit'];result['jidt_jar_sha256']=build['jar_sha256']
            result['input_sha256']=digest(path)
            result['source_timestamp_sha256']=hashlib.sha256('\n'.join(data.timestamp_utc.astype(str)).encode()).hexdigest()
            result['first_source_timestamp_utc']=str(data.timestamp_utc.iloc[0]);result['last_source_timestamp_utc']=str(data.timestamp_utc.iloc[-1])
            result['java_time_indices_verified']=True
            cache[identity]=result.copy();return result
        original=pd.read_csv(ROOT/'results/primary_information/primary_information_summary.csv')
        cleaned={};matched={};baseline_checks=[];matching_checks=[]
        # Complete ALL preflight and baseline reproduction before sensitivity runs.
        for site in PAIRS:
            data=pd.read_csv(ROOT/f'data/processed/{site}.csv');data['timestamp_utc']=pd.to_datetime(data.timestamp_utc,utc=True);data['near_timestamp_utc']=data.timestamp_utc
            cleaned[site]=data
            actual=estimate(site,data,'original_zero_lag')
            for row in actual.itertuples():
                old=original.loc[original.site.eq(site)&original.measure.eq(row.measure_name)].iloc[0]
                assert row.sample_size==old.sample_size
                if abs(row.nats-old.nats)>1e-12:raise RuntimeError('Step 7 baseline reproduction failed')
                baseline_checks.append({'site':site,'measure':row.measure,'original_nats':old.nats,'reproduced_nats':row.nats,'difference_nats':row.nats-old.nats,'sample_size':row.sample_size,'passed':True})
            matched[site]=load_lags(site)
            zero=matched[site][0]
            np.testing.assert_array_equal(zero.timestamp_utc.to_numpy(),data.timestamp_utc.to_numpy())
            np.testing.assert_allclose(zero[COLS],data[COLS],rtol=0,atol=1e-14)
            for lag,frame in matched[site].items():
                assert (frame.near_timestamp_utc-frame.timestamp_utc).eq(pd.Timedelta(hours=lag)).all()
                assert frame.timestamp_utc.dt.minute.eq(0).all()
                target_minute=30 if lag==.5 else 0
                assert frame.near_timestamp_utc.dt.minute.eq(target_minute).all()
                matching_checks.append({'site':site,'lag_hours':lag,'sample_size':len(frame),'source_hourly':True,'target_minute':target_minute,'matching_exact':True})
        pd.DataFrame(baseline_checks).to_csv(validation/'baseline_reproduction.csv',index=False)
        pd.DataFrame(matching_checks).to_csv(validation/'lag_matching.csv',index=False)
        gate={'passed':True,'baseline_reproduction_passed':True,'baseline_max_abs_difference_nats':max(abs(r['difference_nats']) for r in baseline_checks),
              'half_hourly_matching_passed':True,'java_configurations_tested':12,'physical_windows_hours':[30,45,60],
              'synthetic_index_units_hours':[1,.5],'real_source_index_units_hours':1,
              'direction_joint_dimensions':[2,1,1],'noise_seed':20261031,'jidt_commit':build['commit'],
              'java_sources_sha256':{name:digest(ROOT/'src/java'/name) for name in java}}
        (validation/'acceptance.json').write_text(json.dumps(gate,indent=2)+'\n')
        outputs=[];counts=[]
        def add(result,factor,cohort,lag):
            result=result.copy();result['analysis']=factor;result['cohort']=cohort;result['lag_hours']=lag;outputs.append(result)
        for site in PAIRS:
            for k in [3,4,6,8]:add(estimate(site,cleaned[site],'original_zero_lag',k,45),'k','original_cleaned',0)
            for window in [30,45,60]:add(estimate(site,cleaned[site],'original_zero_lag',4,window),'theiler','original_cleaned',0)
            common=set.intersection(*(set(d.timestamp_utc) for d in matched[site].values()))
            if not common:raise RuntimeError('No common source timestamps across lags')
            for lag,data in matched[site].items():
                for cohort in ['all_available','common_source_timestamps']:
                    frame=data if cohort=='all_available' else data.loc[data.timestamp_utc.isin(common)].reset_index(drop=True)
                    key=f'lag{lag:g}_{cohort}'
                    result=estimate(site,frame,key,4,45)
                    add(result,'lag',cohort,lag)
                    counts.append({'site':site,'cohort':cohort,'lag_hours':lag,'sample_size':len(frame),
                                   'first_source_timestamp_utc':str(frame.timestamp_utc.min()),'last_source_timestamp_utc':str(frame.timestamp_utc.max()),
                                   'first_near_timestamp_utc':str(frame.near_timestamp_utc.min()),'last_near_timestamp_utc':str(frame.near_timestamp_utc.max())})
            print(f'{site}: baseline reproduced, k/window/lag runs complete; common N={len(common)}',flush=True)
        results=pd.concat(outputs,ignore_index=True)
        if len(results)!=90:raise RuntimeError('Missing sensitivity rows')
        first=['site','analysis','cohort','measure','measure_name','sample_size','k','lag_hours','theiler_hours','nats','bits']
        results=results[first+[c for c in results if c not in first]]
        results.to_csv(OUT/'all_sensitivity_results.csv',index=False)
        for factor in ['k','theiler','lag']:results.loc[results.analysis.eq(factor)].to_csv(OUT/f'{factor}_sensitivity.csv',index=False)
        pd.DataFrame(counts).to_csv(OUT/'lag_sample_counts.csv',index=False)
        (OUT/'settings.json').write_text(json.dumps({'baseline':{'k':4,'theiler_hours':45,'lag_hours':0},'k_values':[3,4,6,8],'lag_hours':LAGS,'theiler_hours':[30,45,60],
                  'normalise':True,'norm_type':'MAX_NORM','noise_std':1e-8,'noise_seed':20261031,'use_gpu':False,
                  'algorithm':'KSG1','build':build,'source_time_indices':'Actual elapsed offshore hours, same set ID 0 across segments; nearshore target times may be half-hourly',
                  'significance_tests_run':False,'unique_java_datasets_and_settings':len(cache),'reported_sensitivity_rows':len(results)},indent=2)+'\n')
        print(results[['site','analysis','cohort','measure','sample_size','k','lag_hours','theiler_hours','bits']].to_string(index=False))
    finally:
        unchanged=all(digest(ROOT/p)==sha for p,sha in before.items())
        (OUT/'preservation_checks.json').write_text(json.dumps({'unchanged':unchanged,'sha256':before},indent=2)+'\n')
        if not unchanged:raise RuntimeError('Protected prior data/code/results changed')


if __name__=='__main__':main()
