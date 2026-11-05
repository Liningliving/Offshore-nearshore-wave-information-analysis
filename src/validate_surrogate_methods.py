"""Surrogate-method validation preflight: methodology and synthetic validation, never full wave tests."""
from pathlib import Path
import json
import hashlib
import subprocess
import numpy as np
import pandas as pd
from primary_information import verify_build, digest
from autocorrelation import hourly_indices
from surrogate_methods import height_neighbours,local_order,compatible_circular_shifts,circular_order,elapsed_acf,p_plus_one

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/surrogate_validation'
VALIDATION=OUT/'validation'
SEED=20261101  # separate from fixed JIDT tie-noise seed 20261031
B=20
REPLICATES=16


def ar1(rng,n,rho):
    innovations=rng.normal(size=n+5000);a=np.empty(len(innovations));a[0]=rng.normal()
    for i in range(1,len(a)):a[i]=rho*a[i-1]+np.sqrt(1-rho*rho)*innovations[i]
    return a[-n:]


def mask_audit():
    result=[]
    for site in ['figure_eight_pools','stockton']:
        d=pd.read_csv(ROOT/f'data/processed/{site}.csv');h=hourly_indices(d.timestamp_utc)
        shifts=compatible_circular_shifts(h)
        # Weekly complete-pattern block permutations: only compare equal masks.
        full=int(h[-1]//168);patterns={}
        for block in range(full):
            pattern=tuple((h[(h>=168*block)&(h<168*(block+1))]-168*block).tolist())
            patterns.setdefault(pattern,[]).append(block)
        movable=sum(len(pattern)*len(blocks) for pattern,blocks in patterns.items() if len(blocks)>1)
        result.append({'site':site,'observations':len(h),'hourly_span':int(h[-1]+1),
                       'minimum_circular_shift_hours':180,'mask_preserving_nonzero_shifts':len(shifts),
                       'weekly_mask_matched_movable_observations':movable,
                       'weekly_mask_matched_fixed_observations':len(h)-movable,
                       'mask_matched_blocks_note':'Same missingness-pattern blocks may be exchanged; all singleton-pattern blocks and the partial final block remain fixed, so this is not a validated full-record independence null.'})
    return result


def main():
    VALIDATION.mkdir(parents=True,exist_ok=True)
    protected=[p for directory in ['data/raw','data/processed','results/preprocessing','results/exploratory_figures','results/primary_information'] for p in (ROOT/directory).rglob('*') if p.is_file()]
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    gate={'main_wave_tests_authorized_by_validation':False,'wave_surrogates_run':0,'main_B':0}
    (OUT/'validation_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    build=verify_build();classes=VALIDATION/'classes';classes.mkdir(exist_ok=True)
    java=['ElapsedHourLoader.java','SharedEstimatorSettings.java','SurrogateValidationEstimator.java','JidtSurrogateAudit.java']
    c=subprocess.run(['javac','-cp',str(ROOT/'tools/jidt/build/infodynamics.jar'),'-d',str(classes),*[str(ROOT/'src/java'/p) for p in java]],capture_output=True,text=True)
    (VALIDATION/'compile.log').write_text(c.stdout+c.stderr);c.check_returncode()
    audit=subprocess.run(['java','-cp',str(classes)+':'+str(ROOT/'tools/jidt/build/infodynamics.jar'),'JidtSurrogateAudit',str(OUT/'jidt_runtime_surrogate_audit.csv')],capture_output=True,text=True)
    (VALIDATION/'runtime_audit.log').write_text(audit.stdout+audit.stderr);audit.check_returncode()
    metadata=[];jobs=[]
    hours=np.arange(1344);hours=hours[~np.isin(hours%24,[5,6])]
    shifts=compatible_circular_shifts(hours)
    assert len(shifts)>0
    for rho in [0,.98]:
        for rep in range(REPLICATES):
            rng=np.random.default_rng(SEED+int(rho*1000)*100+rep)
            z=ar1(rng,1344,rho);ex=ar1(rng,1344,rho);ey=ar1(rng,1344,rho)
            for measure in ['mi','period','direction']:
                for dependence in ['null_hypothesis','dependent']:
                    dependent=dependence=='dependent'
                    x=.8*z+ex;y=.8*z+(0.8*ex if dependent else 0)+ey
                    theta=1.2*z+ex
                    if measure=='mi':ho=ex;y=(.8*ex if dependent else 0)+ey
                    else:ho=z
                    values=np.column_stack([ho,y,x,np.cos(theta),np.sin(theta)])[hours]
                    label='null' if dependence=='null_hypothesis' else dependence
                    key=f'{measure}_rho{rho:g}_{label}_r{rep:02d}'
                    data=VALIDATION/f'{key}_data.csv';orders_path=VALIDATION/f'{key}_orders.csv';output=VALIDATION/f'{key}_estimates.csv'
                    with data.open('w') as f:
                        for h,row in zip(hours,values):f.write(str(h)+','+','.join(format(v,'.17g') for v in row)+'\n')
                    local=height_neighbours(values[:,0],5) if measure!='mi' else None
                    orders=[];acfs=[];correlations=[];reuse=[];selfrates=[];distances=[]
                    source=values[:,0] if measure=='mi' else values[:,2] if measure=='period' else values[:,3]
                    for b in range(B):
                        order=circular_order(hours,int(rng.choice(shifts))) if measure=='mi' else local_order(local,rng)
                        orders.append(order);acfs.append(elapsed_acf(hours,source[order]))
                        if measure!='mi':correlations.append(float(np.corrcoef(source[order],values[:,0])[0,1]))
                        reuse.append(1-len(np.unique(order))/len(order));selfrates.append(float(np.mean(order==np.arange(len(order)))))
                        if measure!='mi':distances.append(float(np.mean(np.abs(values[order,0]-values[:,0]))))
                    np.savetxt(orders_path,np.array(orders),delimiter=',',fmt='%d')
                    jobs.append('\t'.join([str(data),str(orders_path),str(output),measure]))
                    metadata.append({'key':key,'measure':measure,'rho':rho,'truth':dependence,'replicate':rep,
                                     'n':len(hours),'B':B,'source_acf_1h':elapsed_acf(hours,source),
                                     'surrogate_mean_acf_1h':float(np.mean(acfs)),
                                     'source_condition_correlation':float(np.corrcoef(source,values[:,0])[0,1]) if measure!='mi' else None,
                                     'surrogate_mean_source_condition_correlation':float(np.mean(correlations)) if correlations else None,
                                     'mean_donor_reuse_fraction':float(np.mean(reuse)),
                                     'mean_unchanged_source_fraction':float(np.mean(selfrates)),
                                     'mean_abs_conditioning_distance':float(np.mean(distances)) if distances else None,
                                     'output_file':str(output.relative_to(ROOT))})
    manifest=VALIDATION/'jobs.tsv';manifest.write_text('\n'.join(jobs)+'\n')
    pd.DataFrame(metadata).to_csv(VALIDATION/'synthetic_design.csv',index=False)
    process=subprocess.Popen(['java','-Xmx2g','-cp',str(classes)+':'+str(ROOT/'tools/jidt/build/infodynamics.jar'),'SurrogateValidationEstimator',str(manifest)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    with (VALIDATION/'java.log').open('w') as log:
        for i,line in enumerate(process.stdout):
            log.write(line);log.flush()
            if i%12==0:print(line.strip(),flush=True)
    if process.wait():raise RuntimeError('Java validation estimator failed; see log')
    for row in metadata:
        estimates=pd.read_csv(ROOT/row['output_file']);observed=float(estimates.iloc[0].nats);null=estimates.iloc[1:].nats.to_numpy()
        assert len(null)==B and estimates.timing_verified.all() and estimates.nearest_neighbours_verified.all()
        row.update(observed_nats=observed,observed_bits=observed/np.log(2),p_plus_one=p_plus_one(observed,null),
                   null_mean_bits=float(np.mean(null)/np.log(2)),null_std_bits=float(np.std(null,ddof=1)/np.log(2)),
                   reject_at_05=p_plus_one(observed,null)<=.05)
    results=pd.DataFrame(metadata);results.to_csv(VALIDATION/'synthetic_results.csv',index=False)
    summary=results.groupby(['measure','rho','truth'],as_index=False).agg(tests=('replicate','size'),rejections=('reject_at_05','sum'),
                    rejection_fraction=('reject_at_05','mean'),mean_source_acf=('source_acf_1h','mean'),mean_surrogate_acf=('surrogate_mean_acf_1h','mean'))
    summary.to_csv(VALIDATION/'synthetic_summary.csv',index=False)
    masks=mask_audit();(OUT/'wave_timestamp_mask_audit.json').write_text(json.dumps(masks,indent=2)+'\n')
    unchanged=all(digest(ROOT/p)==sha for p,sha in before.items());assert unchanged
    (OUT/'preservation_checks.json').write_text(json.dumps({'unchanged':unchanged,'sha256':before},indent=2)+'\n')
    gate.update(status='stopped_before_wave_pilot_and_main',B_synthetic_pilot=B,synthetic_replicates=REPLICATES,
                surrogate_seed_base=SEED,estimator_noise_seed=20261031,source_commit=build['commit'],
                reasons=['No admissible all-observation, mask-preserving circular shift for either wave record; block-pattern rearrangements leave aligned observations fixed.',
                         'Runge-style pointwise local permutation does not preserve predictor temporal structure; calibration must be accepted before any conditional-significance claims.'],
                synthetic_summary=summary.to_dict(orient='records'),wave_mask_audit=masks)
    (OUT/'validation_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    print(summary.to_string(index=False));print(json.dumps(masks,indent=2))


if __name__=='__main__':main()
