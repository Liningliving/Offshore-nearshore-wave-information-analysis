"""Read-only audit of saved between-site pilot results. No JIDT or resampling."""
from artifact_paths import resolve_artifact_path
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/between_site_method_assessment'
PILOT=ROOT/'research/between_site_subsampling/validation'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    protected=[p for folder in ['data/raw','data/processed','results/preprocessing','results/primary_information','research/surrogate_validation','results/sensitivity_analysis','research/between_site_subsampling'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    checks=pd.read_csv(PILOT/'candidate_interval_checks.csv')
    records=[];diagnostics=[]
    names={'equal_information_same_persistence':'Equal information; AR(0.90), AR(0.90)',
           'equal_information_different_persistence':'Equal information; AR(0.80), AR(0.97)',
           'known_information_difference':'Known difference; AR(0.80), AR(0.97)'}
    for (scenario,measure),group in checks.groupby(['scenario','measure']):
        null=bool(group.true_delta_nats.eq(0).all());n=len(group)
        records.append({'scenario':scenario,'setting':names[scenario],'measure':measure,'experiments':n,
                        'true_delta_bits':float(group.true_delta_nats.iloc[0]/np.log(2)),
                        'covered_experiments':int(group.truth_covered.sum()),'coverage':float(group.truth_covered.mean()),
                        'zero_exclusions':int(group.zero_excluded.sum()),
                        'false_positive_rate':float(group.zero_excluded.mean()) if null else np.nan,
                        'known_difference_detection_rate':float(group.zero_excluded.mean()) if not null else np.nan,
                        'nominal_coverage':.95,'synthetic_only':True})
        stds=[];fractions=[];centres=[]
        for row in group.itertuples():
            saved=pd.read_csv(resolve_artifact_path(row.output_file))
            cols=['height_nats','period_nats','direction_nats'];i=['height','period','direction'].index(measure)
            full_a=saved.loc[saved.draw.eq(-1)&saved.site.eq('A')].iloc[0]
            full_b=saved.loc[saved.draw.eq(-1)&saved.site.eq('B')].iloc[0]
            a=saved.loc[saved.draw.ge(0)&saved.site.eq('A')].sort_values('draw')
            b=saved.loc[saved.draw.ge(0)&saved.site.eq('B')].sort_values('draw')
            # Reproduce the saved arithmetic only; no new blocks/estimator calls.
            ea=np.sqrt(a.n.to_numpy()/full_a.n)*(a[cols[i]].to_numpy()-full_a[cols[i]])
            eb=np.sqrt(b.n.to_numpy()/full_b.n)*(b[cols[i]].to_numpy()-full_b[cols[i]])
            errors=(ea-eb)*(1 if measure=='height' else -1)
            stds.append(float(np.std(errors,ddof=1)));centres.append(float(np.mean(errors)))
            fractions.extend((a.n/full_a.n).tolist()+(b.n/full_b.n).tolist())
            observed=float(row.estimated_delta_nats)
            np.testing.assert_allclose([observed-np.quantile(errors,.975),observed-np.quantile(errors,.025)],
                                       [row.candidate_lower_nats,row.candidate_upper_nats],rtol=1e-12,atol=1e-14)
        true_error=group.estimated_delta_nats-group.true_delta_nats
        empirical_sd=float(true_error.std(ddof=1));candidate_sd=float(np.mean(stds))
        diagnostics.append({'scenario':scenario,'measure':measure,'experiments':n,
                            'empirical_mean_full_contrast_error_bits':float(true_error.mean()/np.log(2)),
                            'empirical_full_contrast_SD_bits':empirical_sd/np.log(2),
                            'mean_candidate_error_SD_bits':candidate_sd/np.log(2),
                            'candidate_to_empirical_SD_ratio':candidate_sd/empirical_sd,
                            'mean_candidate_error_centre_bits':float(np.mean(centres)/np.log(2)),
                            'mean_retained_block_fraction':float(np.mean(fractions)),
                            'min_retained_block_fraction':float(min(fractions)),
                            'max_retained_block_fraction':float(max(fractions)),
                            'interpretation':'Diagnostic from only 12 simulations; not a uniquely identified cause or a wave uncertainty estimate'})
    order={'equal_information_same_persistence':0,'equal_information_different_persistence':1,'known_information_difference':2}
    methods={'height':0,'period':1,'direction':2}
    records.sort(key=lambda r:(order[r['scenario']],methods[r['measure']]))
    pd.DataFrame(records).to_csv(OUT/'pilot_coverage_by_setting.csv',index=False)
    pd.DataFrame(diagnostics).to_csv(OUT/'pilot_error_diagnostics.csv',index=False)
    inventory=[
        {'method':'Independent physical-time moving-window subsampling with separate-site root-N scaling','actually_run_between_sites':True,'status':'Failed initial calibration screen'},
        {'method':'Ordinary i.i.d. or moving/stationary with-replacement bootstrap','actually_run_between_sites':False,'status':'Not run; duplicate-observation effects on KSG not resolved'},
        {'method':'Site-label or individual-observation permutation','actually_run_between_sites':False,'status':'Not run; exchangeability and temporal assumptions not justified'},
        {'method':'Fixed-b calibrated or studentized subsampling','actually_run_between_sites':False,'status':'Literature assessed; required limit/bias assumptions not established for current estimators'},
        {'method':'Holmes–Nemenman variance extrapolation','actually_run_between_sites':False,'status':'Literature assessed; not directly validated for these dependent MI/CMI comparisons'},
        {'method':'Step 8 within-site surrogate procedures','actually_run_between_sites':False,'status':'Separate within-site problem; not a direct between-site test'},
    ]
    pd.DataFrame(inventory).to_csv(OUT/'methods_inventory.csv',index=False)
    unchanged=all(sha(ROOT/p)==h for p,h in before.items());assert unchanged
    (OUT/'assessment_manifest.json').write_text(json.dumps({'existing_files_unchanged':unchanged,'original_sha256':before,
         'new_jidt_runs':0,'new_synthetic_experiments':0,'new_wave_confidence_intervals':False,'new_wave_p_values':False,
         'decision':'No off-the-shelf inferential procedure accepted; no larger new simulation launched during this assessment'},indent=2)+'\n')
    print(pd.DataFrame(records)[['setting','measure','covered_experiments','experiments','false_positive_rate','known_difference_detection_rate']].to_string(index=False))


if __name__=='__main__':main()
