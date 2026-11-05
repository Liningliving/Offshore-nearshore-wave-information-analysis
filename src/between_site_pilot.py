"""Calibrate a candidate unequal-sample time-block comparison; no wave CIs by default."""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
import pandas as pd
from primary_information import verify_build,digest

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/between_site_subsampling'
V=OUT/'validation'
SEED=20261102
REPS=12
B=39
FRACTION=.25


def gaussian_truth(coefficients):
    a,b,c=coefficients;res=b*b+c*c+1
    return np.array([.5*np.log((a*a+res)/res),.5*np.log(res/(c*c+1)),.5*np.log(res/(b*b+1))])


def ar(rng,n,phi):
    noise=rng.normal(size=n);x=np.empty(n);x[0]=rng.normal()
    for i in range(1,n):x[i]=phi*x[i-1]+np.sqrt(1-phi*phi)*noise[i]
    return x


def synthetic_site(rng,span,phi,coefficients,site):
    # Independent stationary standard-normal latent AR processes.
    z,p,g,e=[ar(rng,span,phi) for _ in range(4)]
    a,b,c=coefficients;theta=2*np.arctan(g+.3*z)
    values=np.column_stack([3+z,3+a*z+b*p+c*g+e,10+.4*z+p,np.cos(theta),np.sin(theta)])
    mask=rng.random(span)>(.08 if site=='A' else .04)
    start=int(.4*span);mask[start:start+int((.06 if site=='A' else .02)*span)]=False
    mask[0]=True;mask[-1]=True
    hours=np.arange(span)[mask]
    return np.column_stack([hours,values[mask]])


def contrast(a,b):
    # A-B for height, B-A for period/direction.
    return (np.asarray(a)-np.asarray(b))*np.array([1,-1,-1])


def candidate_root_interval(full_a,full_b,blocks_a,blocks_b,n_a,n_b,m_a,m_b):
    observed=contrast(full_a,full_b)
    # Candidate root-N laws separately by site; not raw block quantiles.
    error_a=np.sqrt(np.asarray(m_a)[:,None]/n_a)*(np.asarray(blocks_a)-full_a)
    error_b=np.sqrt(np.asarray(m_b)[:,None]/n_b)*(np.asarray(blocks_b)-full_b)
    errors=contrast(error_a,error_b)
    lo=observed-np.quantile(errors,.975,axis=0)
    hi=observed-np.quantile(errors,.025,axis=0)
    return observed,lo,hi,errors


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--replicates',type=int,default=REPS)
    args=parser.parse_args();V.mkdir(parents=True,exist_ok=True)
    protected=[p for d in ['data/raw','data/processed','results/preprocessing','results/exploratory_figures','results/primary_information','research/surrogate_validation','results/sensitivity_analysis'] for p in (ROOT/d).rglob('*') if p.is_file()]
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    plan={'status':'pilot_not_yet_accepted','nominal_coverage':.95,'pilot_failure_rule':'Any scenario/measure empirical coverage below 0.80, or runtime/time metadata failure, rejects this candidate. Passing this screen alone requires expanded calibration, not automatic wave inference.',
          'method':'paired independent physical-time moving-window subsampling, no duplicated rows within a draw; root-N error scaling separately by site',
          'fraction_of_each_record_span':FRACTION,'resamples_per_record_pair':B,'replicates_per_scenario':args.replicates,
          'seed':SEED,'estimator_noise_seed':20261031,'main_wave_inference_run':False}
    (V/'pilot_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    build=verify_build();classes=V/'classes';classes.mkdir(exist_ok=True)
    sources=['ElapsedHourLoader.java','SharedEstimatorSettings.java','BetweenSiteSubsamplingPilot.java']
    result=subprocess.run(['javac','-cp',str(ROOT/build['jar']),'-d',str(classes),*[str(ROOT/'src/java'/f) for f in sources]],capture_output=True,text=True)
    (V/'compile.log').write_text(result.stdout+result.stderr);result.check_returncode()
    jobs=[];design=[];truth_rows=[]
    coeff_a=(1.2,.3,.4)
    scenarios=[('equal_information_same_persistence',(.9,.9),coeff_a),
               ('equal_information_different_persistence',(.8,.97),coeff_a),
               ('known_information_difference',(.8,.97),(.7,.65,.8))]
    for scenario,(phi_a,phi_b),coeff_b in scenarios:
        true=contrast(gaussian_truth(coeff_a),gaussian_truth(coeff_b))
        for measure,value in zip(['height','period','direction'],true):truth_rows.append({'scenario':scenario,'measure':measure,'true_delta_nats':value,'true_delta_bits':value/np.log(2)})
        for rep in range(args.replicates):
            scenario_id=[s[0] for s in scenarios].index(scenario)
            rng=np.random.default_rng(SEED+scenario_id*10000+rep)
            a=synthetic_site(rng,3600,phi_a,coeff_a,'A');b=synthetic_site(rng,5400,phi_b,coeff_b,'B')
            key=f'{scenario}_r{rep:02d}'
            paths=[]
            for site,data in [('A',a),('B',b)]:
                path=V/f'{key}_{site}.csv';np.savetxt(path,data,delimiter=',',fmt=['%d']+['%.17g']*5);paths.append(path)
            blocks=[]
            for _ in range(B):
                wa=int(3600*FRACTION);wb=int(5400*FRACTION)
                sa=int(rng.integers(0,3600-wa+1));sb=int(rng.integers(0,5400-wb+1));blocks.append([sa,sa+wa,sb,sb+wb])
            block_path=V/f'{key}_blocks.csv';np.savetxt(block_path,blocks,delimiter=',',fmt='%d')
            estimates=V/f'{key}_estimates.csv'
            jobs.append('\t'.join(map(str,[*paths,block_path,estimates])))
            design.append({'scenario':scenario,'replicate':rep,'phi_A':phi_a,'phi_B':phi_b,'N_A':len(a),'N_B':len(b),'T_A':3600,'T_B':5400,'block_A_hours':900,'block_B_hours':1350,'output_file':str(estimates.relative_to(ROOT))})
    pd.DataFrame(design).to_csv(V/'synthetic_design.csv',index=False);pd.DataFrame(truth_rows).to_csv(V/'analytic_truth.csv',index=False)
    manifest=V/'jobs.tsv';manifest.write_text('\n'.join(jobs)+'\n')
    process=subprocess.Popen(['java','-Xmx2g','-cp',str(classes)+':'+str(ROOT/build['jar']),'BetweenSiteSubsamplingPilot',str(manifest)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    with (V/'java.log').open('w') as log:
        for line in process.stdout:log.write(line);log.flush();print(line.strip(),flush=True)
    if process.wait():raise RuntimeError('Java calibration failed; inspect log')
    results=[]
    for d in design:
        e=pd.read_csv(ROOT/d['output_file']);assert e.exact_time_verified.all()
        full_a=e.loc[e.draw.eq(-1)&e.site.eq('A')].iloc[0];full_b=e.loc[e.draw.eq(-1)&e.site.eq('B')].iloc[0]
        a=e.loc[e.draw.ge(0)&e.site.eq('A')].sort_values('draw');b=e.loc[e.draw.ge(0)&e.site.eq('B')].sort_values('draw')
        cols=['height_nats','period_nats','direction_nats']
        observed,lo,hi,errors=candidate_root_interval(full_a[cols].to_numpy(float),full_b[cols].to_numpy(float),a[cols].to_numpy(),b[cols].to_numpy(),int(full_a.n),int(full_b.n),a.n.to_numpy(),b.n.to_numpy())
        for i,m in enumerate(['height','period','direction']):
            true=next(t['true_delta_nats'] for t in truth_rows if t['scenario']==d['scenario'] and t['measure']==m)
            results.append({**d,'measure':m,'true_delta_nats':true,'estimated_delta_nats':observed[i],'candidate_lower_nats':lo[i],'candidate_upper_nats':hi[i],
                            'truth_covered':bool(lo[i]<=true<=hi[i]),'zero_excluded':bool(lo[i]>0 or hi[i]<0),
                            'candidate_width_nats':hi[i]-lo[i],'mean_block_root_error_nats':float(errors[:,i].mean()),'block_min_N_A':int(a.n.min()),'block_min_N_B':int(b.n.min())})
    results=pd.DataFrame(results);results.to_csv(V/'candidate_interval_checks.csv',index=False)
    summary=results.groupby(['scenario','measure'],as_index=False).agg(replicates=('replicate','size'),coverage=('truth_covered','mean'),zero_exclusion_rate=('zero_excluded','mean'),mean_interval_width_nats=('candidate_width_nats','mean'),mean_root_error_nats=('mean_block_root_error_nats','mean'))
    summary.to_csv(V/'calibration_summary.csv',index=False)
    failure=bool((summary.coverage<.8).any())
    verdict={**plan,'status':'rejected_by_pilot' if failure else 'requires_expanded_calibration',
             'calibration_screen_passed':not failure,'method_accepted_for_wave_inference':False,
             'jar_sha256':build['jar_sha256'],'jidt_commit':build['commit'],'summary':summary.to_dict(orient='records')}
    (OUT/'inference_gate.json').write_text(json.dumps(verdict,indent=2)+'\n')
    unchanged=all(digest(ROOT/p)==sha for p,sha in before.items());assert unchanged
    (OUT/'preservation_checks.json').write_text(json.dumps({'unchanged':unchanged,'sha256':before},indent=2)+'\n')
    print(summary.to_string(index=False));print(verdict['status'])


if __name__=='__main__':main()
