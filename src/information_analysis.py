"""Run JIDT 1.6.1 primary estimates, surrogate diagnostics and one-factor sensitivities."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import time
import numpy as np
import pandas as pd
from preprocess import PAIRS, DATA, numeric

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'outputs/results'
RUNS=RESULTS/'information_runs'
INPUTS=RESULTS/'information_inputs'
MEASURES=('mi_height','cmi_period','cmi_direction')
COLUMNS=['Ho','Hn','Tp_o','Dx','Dy']
SEED=20261030


def match_lag(site, lag):
    token, station, filename=PAIRS[site]
    path,=DATA.glob(f'*{token}*/*Parameters.csv')
    near=pd.read_csv(path); off=pd.read_csv(DATA/filename,comment='#')
    numeric(near,['Hsig','Qflag']); numeric(off,['WHTH','WPPE','WPDI','WAVE_quality_control'])
    near['near_timestamp_utc']=pd.to_datetime(near.Time,format='%d-%b-%Y %H:%M:%S').dt.tz_localize('Etc/GMT-10').dt.tz_convert('UTC')
    off['timestamp_utc']=pd.to_datetime(off.TIME,utc=True)
    near['timestamp_utc']=near.near_timestamp_utc-pd.Timedelta(hours=lag)
    near=near.loc[near.Qflag.eq(1),['timestamp_utc','near_timestamp_utc','Hsig']]
    off=off.loc[off.WAVE_quality_control.eq(1),['timestamp_utc','WHTH','WPPE','WPDI']]
    d=off.merge(near,on='timestamp_utc',validate='one_to_one').rename(columns={'WHTH':'Ho','Hsig':'Hn','WPPE':'Tp_o','WPDI':'theta_deg'})
    d=d.dropna(subset=['Ho','Hn','Tp_o','theta_deg']).sort_values('timestamp_utc').reset_index(drop=True)
    if d.timestamp_utc.duplicated().any(): raise ValueError('Duplicate offshore times')
    if not d.timestamp_utc.eq(d.timestamp_utc.dt.floor('h')).all():
        raise ValueError('Conservative hourly row exclusion requires clock-hour offshore timestamps')
    if not np.isfinite(d[['Ho','Hn','Tp_o','theta_deg']]).all().all(): raise ValueError('Nonfinite inputs')
    if not (d[['Ho','Hn']].ge(0).all().all() and d.Tp_o.gt(0).all() and d.theta_deg.between(0,360).all()): raise ValueError('Invalid ranges')
    radians=np.deg2rad(d.theta_deg); d['Dx']=np.cos(radians); d['Dy']=np.sin(radians)
    return d


def exclusion_audit(data, window):
    t=pd.DatetimeIndex(data.timestamp_utc).asi8 / 3.6e12
    exact=0; indexed=0; extra=0
    for i in range(len(t)):
        exact+=int(np.searchsorted(t,t[i]+window,side='right')-i-1)
        stop=min(len(t),i+window+1)
        indexed+=stop-i-1
        extra+=int(np.count_nonzero(t[i+1:stop]-t[i]>window))
    return {'physical_pairs_within_window':exact,'row_index_excluded_pairs':indexed,
            'extra_pairs_excluded_across_gaps':extra,
            'extra_fraction_of_index_exclusions':extra/indexed if indexed else 0}


def write_input(data,key):
    raw=data[COLUMNS].to_numpy(float); means=raw.mean(axis=0); std=raw.std(axis=0,ddof=1)
    if (std<=0).any(): raise ValueError('Constant analysis variable')
    # Explicit seeded tie-breaking; same perturbed observations reused for k/window changes.
    values=(raw-means)/std
    values+=np.random.default_rng(SEED).normal(0,1e-8,values.shape)
    path=INPUTS/f'{key}.csv'; np.savetxt(path,values,delimiter=',',fmt='%.17g')
    data[['timestamp_utc','near_timestamp_utc']].to_csv(INPUTS/f'{key}_timestamps.csv',index=False)
    return path, {'means':dict(zip(COLUMNS,means)), 'sample_std':dict(zip(COLUMNS,std)),
                  'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar',type=Path,default=Path('/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar'))
    parser.add_argument('--surrogates',type=int,default=199)
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--allow-conservative-index-window', action='store_true',
                        help='Explicitly opt into the earlier approximate 45-row analysis; not an exact 45-hour implementation')
    args=parser.parse_args()
    if not args.allow_conservative_index_window:
        parser.error('Exact 45-hour integration failed for JIDT 1.6.1: this runner uses retained-row indices. Main analysis is blocked by default. The --allow-conservative-index-window flag explicitly opts into the earlier approximation; it does not fix elapsed-time exclusion.')
    for p in [RUNS,INPUTS]: p.mkdir(parents=True,exist_ok=True)
    if args.surrogates<1: parser.error('At least one surrogate required')
    subprocess.run(['javac','-cp',str(args.jar),'-d',str(RUNS),str(ROOT/'src/java/WaveInformation.java')],check=True)
    lag_values=(0,.5,1,2)
    summaries=[]; diagnostics=[]; input_metadata={}; started=time.time()
    for site in PAIRS:
        datasets={lag:match_lag(site,lag) for lag in lag_values}
        baseline=pd.read_csv(ROOT/f'outputs/cleaned/{site}.csv')
        assert len(datasets[0])==len(baseline)
        np.testing.assert_allclose(datasets[0][COLUMNS],baseline[COLUMNS],rtol=1e-12,atol=1e-12)
        common=set.intersection(*(set(d.timestamp_utc) for d in datasets.values()))
        for lag,data in datasets.items():
            data['common_lag_timestamp']=data.timestamp_utc.isin(common)
            for cohort in ['available','common']:
                subset=data if cohort=='available' else data.loc[data.common_lag_timestamp].reset_index(drop=True)
                key=f'{site}_lag{lag:g}_{cohort}'
                path,meta=write_input(subset,key); input_metadata[key]=meta
                settings=[('baseline',4,45)] if lag==0 and cohort=='available' else []
                if not args.pilot:
                    if lag==0 and cohort=='available':
                        settings += [('k',k,45) for k in [3,6,8]]
                        settings += [('window',4,w) for w in [0,23,90]]
                    else: settings += [('lag' if cohort=='available' else 'lag_common',4,45)]
                if not settings: continue
                for factor,k,w in settings:
                    diagnostics.append({'site':site,'lag_hours':lag,'cohort':cohort,'n':len(subset),'k':k,'window_rows':w,**exclusion_audit(subset,w)})
                    for measure in MEASURES:
                        b=(9 if args.pilot else args.surrogates) if factor=='baseline' else 0
                        bins=0 if measure=='mi_height' else 50
                        variants=[('primary',b,bins)]
                        if factor=='baseline' and not args.pilot and measure!='mi_height':
                            variants += [('unrestricted_reference',99,0),('conditional_bins25',99,25),('conditional_bins100',99,100)]
                        for variant,b,bins in variants:
                            runkey=f'{key}_{factor}_k{k}_w{w}_{measure}_{variant}_b{b}'
                            output=RUNS/f'{runkey}.csv'
                            command=['java','-Xmx2g','-cp',str(RUNS)+':'+str(args.jar),'WaveInformation',str(path),str(output),measure,str(k),str(w),str(b),str(bins),str(SEED)]
                            tick=time.time()
                            fingerprint=hashlib.sha256((json.dumps(command) + meta['input_sha256']
                                + hashlib.sha256(args.jar.read_bytes()).hexdigest()
                                + hashlib.sha256((ROOT/'src/java/WaveInformation.java').read_bytes()).hexdigest()).encode()).hexdigest()
                            stamp=RUNS/f'{runkey}.sha256'
                            if not (output.exists() and stamp.exists() and stamp.read_text()==fingerprint):
                                process=subprocess.run(command,text=True,capture_output=True)
                                (RUNS/f'{runkey}.log').write_text(process.stdout+process.stderr)
                                if process.returncode: raise RuntimeError(process.stdout+process.stderr)
                                stamp.write_text(fingerprint)
                            values=pd.read_csv(output); observed=float(values.iloc[0].nats)
                            null=values.loc[values.kind.eq('surrogate'),'nats'].to_numpy()
                            row={'site':site,'factor':factor,'cohort':cohort,'lag_hours':lag,'measure':measure,'k':k,'window_rows':w,'n':len(subset),
                                 'variant':variant,'conditioning_bins':bins,'surrogates':len(null),'nats':observed,'bits':observed/np.log(2),
                                 'p_plus_one':(1+np.count_nonzero(null>=observed))/(len(null)+1) if len(null) else np.nan,
                                 'surrogate_mean_bits':float(null.mean()/np.log(2)) if len(null) else np.nan,
                                 'surrogate_q95_bits':float(np.quantile(null,.95)/np.log(2)) if len(null) else np.nan,
                                 'surrogate_min_p':1/(len(null)+1) if len(null) else np.nan,'output_file':str(output.relative_to(ROOT))}
                            summaries.append(row)
                            pd.DataFrame(summaries).to_csv(RESULTS/('information_pilot.csv' if args.pilot else 'information_results.csv'),index=False)
                            print(f'{site} {factor} lag={lag:g} {cohort} {measure} {variant} N={len(subset)} bits={row["bits"]:.6f} p={row["p_plus_one"]} ({time.time()-tick:.1f}s)',flush=True)
    pd.DataFrame(diagnostics).to_csv(RESULTS/'information_exclusion_audit.csv',index=False)
    metadata={'jar':str(args.jar),'jar_sha256':hashlib.sha256(args.jar.read_bytes()).hexdigest(),'jidt_version':'1.6.1',
              'algorithm':'CPU Kraskov algorithm 1, MI and joint-space CMI','k_baseline':4,'window_baseline_rows':45,
              'normalisation':'external per-column z score, sample standard deviation ddof=1; JIDT NORMALISE=false',
              'noise':'external Gaussian std 1e-8 in standardized units; JIDT NOISE_LEVEL_TO_ADD=0',
              'noise_seed':SEED,'surrogate_seed':SEED,'threads':4,'gpu':False,
              'window_semantics':'v1.6.1 single-set row-index exclusion; conservative physical-time lower bound, quantified extra exclusions across gaps',
              'lag_hours':lag_values,'lag_definition':'offshore at t predicts nearshore at t+lag; raw QC-retained files rematched on actual timestamps',
              'lag_justification':'0, 0.5, 1 and 2 h bracket short delays at available nearshore resolution; exploratory alignment sensitivity, not a travel-time estimate. Widely separated Sydney–Stockton need not share a direct propagation path.',
              'surrogate_method':'MI unrestricted source permutation; CMI joint predictor-row permutations within 50 rank-based equal-count offshore-height groups; references with unrestricted, 25 and 100 groups',
              'p_value':'upper tail (1 + count(null >= observed))/(B+1); approximate diagnostic under temporal dependence and coarse conditioning, not confirmatory conditional-independence test',
              'units':'raw nats, bits = nats / ln(2)','inputs':input_metadata,'elapsed_seconds':time.time()-started}
    (RESULTS/('information_pilot_settings.json' if args.pilot else 'information_settings.json')).write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__': main()
