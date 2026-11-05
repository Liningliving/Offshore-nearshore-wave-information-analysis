"""Report surrogate-method validation; never fabricate wave p-values/distributions."""
from artifact_paths import resolve_artifact_path
from pathlib import Path
import json
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'ass2-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/surrogate_validation'


def table(d):
    return '| '+' | '.join(d.columns)+' |\n|'+'|'.join(['---']*len(d.columns))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in d.itertuples(index=False,name=None))+'\n'


def main():
    gate=json.loads((OUT/'validation_gate.json').read_text())
    if gate['main_wave_tests_authorized_by_validation']:raise RuntimeError('This report is only for the stopped validation stage')
    original=pd.read_csv(ROOT/'results/primary_information/primary_information_summary.csv')
    d=original.copy()
    d['null_hypothesis']=[('Ho independent of Hn' if m=='I(Ho;Hn)' else 'Tp_o independent of Hn given Ho' if 'Tp_o' in m else '(Dx,Dy) jointly independent of Hn given Ho') for m in d.measure]
    d['candidate_surrogate_method']=['mask-preserving exact-hour circular shift' if m=='I(Ho;Hn)' else 'Runge 2018 Algorithm 1 nearest-Ho local resampling, k_perm=5' for m in d.measure]
    d['status']='not_tested_validity_gate_unresolved'
    d['surrogates']=0;d['planned_main_surrogates']=199;d['synthetic_pilot_B']=20
    d['surrogate_seed_base']=gate['surrogate_seed_base']
    for column in ['surrogate_mean_nats','surrogate_std_nats','surrogate_q025_nats','surrogate_q95_nats','surrogate_q975_nats','surrogate_mean_bits','p_unadjusted','p_holm']:
        d[column]=np.nan
    d['methodological_limitations']=[('No admissible large mask-preserving circular shifts; equal-gap-pattern weekly block swaps leave most/all alignment fixed. Missing-data interpolation or observation changes not authorized.' if m=='I(Ho;Hn)' else 'Local donors approximate conditioning on Ho, can reuse donors, leave some values fixed and do not preserve predictor autocorrelation. Small synthetic checks do not establish calibrated time-series conditional p-values.') for m in d.measure]
    d.to_csv(OUT/'wave_significance_status.csv',index=False)
    synthetic=pd.read_csv(OUT/'validation/synthetic_results.csv')
    summary=pd.read_csv(OUT/'validation/synthetic_summary.csv')
    fig,axes=plt.subplots(4,3,figsize=(13,13))
    for r,(rho,truth) in enumerate([(0,'null_hypothesis'),(0,'dependent'),(.98,'null_hypothesis'),(.98,'dependent')]):
        for c,measure in enumerate(['mi','period','direction']):
            row=synthetic.loc[synthetic.rho.eq(rho)&synthetic.truth.eq(truth)&synthetic.measure.eq(measure)&synthetic.replicate.eq(0)].iloc[0]
            values=pd.read_csv(resolve_artifact_path(row.output_file));observed=values.iloc[0].bits;null=values.iloc[1:].bits
            ax=axes[r,c];ax.hist(null,bins=10,color='tab:blue',alpha=.7);ax.axvline(observed,color='tab:red',label='Synthetic observed')
            ax.set(title=f'{measure}, rho={rho:g}, {truth}',xlabel='Bits',ylabel='Surrogate count');ax.legend(fontsize=7)
    fig.suptitle('Synthetic validation only: replicate 0, B=20; no wave significance results')
    fig.tight_layout();fig.savefig(OUT/'synthetic_surrogate_distributions.png',dpi=150);plt.close(fig)
    selected=summary.loc[summary.rho.eq(.98)&summary.truth.eq('null_hypothesis')]
    fig,ax=plt.subplots(figsize=(8,4));x=np.arange(len(selected))
    ax.bar(x-.18,selected.mean_source_acf,.35,label='Original synthetic source')
    ax.bar(x+.18,selected.mean_surrogate_acf,.35,label='Mean surrogate source')
    ax.set(xticks=x,xticklabels=selected.measure,ylabel='One-hour endpoint autocorrelation',title='Synthetic temporal-preservation diagnostic (rho=0.98)');ax.legend();fig.tight_layout();fig.savefig(OUT/'synthetic_temporal_preservation.png',dpi=150);plt.close(fig)
    observed=d[['site','measure','sample_size','nats','bits','status']].copy()
    observed.nats=observed.nats.map(lambda x:f'{x:.9f}');observed.bits=observed.bits.map(lambda x:f'{x:.9f}')
    summary_show=summary[['measure','rho','truth','tests','rejections','mean_source_acf','mean_surrogate_acf']].copy()
    for c in ['mean_source_acf','mean_surrogate_acf']:summary_show[c]=summary_show[c].map(lambda x:f'{x:.3f}')
    text='''# Surrogate-method validation — full analysis stopped

**No wave significance tests were run.** The validity gate remains unresolved, so there was no wave-data pilot and no 199-surrogate main analysis. The summary CSV has the six unchanged Step 7 estimates, B=0, and missing p-values, not invented or zero p-values. Holm adjustment and wave surrogate-distribution plots are consequently unavailable. The saved distribution plots are explicitly synthetic validation only.

## JIDT audit: source and actual Java runtime

The Step 7 jar is the unmodified official source snapshot at commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456`, identified by the same jar hash in its build manifest. The actual subclasses matter:

- MI `computeSignificance(B)` generates unrestricted random orderings. Its KSG1 override actually rearranges **variable 2 (Hn)** despite the base documentation describing source shuffling. It retains the custom set/time arrays while rebuilding affected search structures. This changes cross-series alignment and destroys Hn temporal ordering.
- CMI defaults to variable 1: Tp_o, or the complete two-column direction array. Ho and Hn remain fixed. Global shuffling destroys source–Ho association as well as the association under test; it is not an appropriate general conditional null.
- CMI `computeSignificance(variable, orders)` clones the calculator, reinitializes it and calls ordinary `setObservations`. This resets custom time points to compressed row indices. In contrast, the optimized single-reordering `computeAverageLocalOfObservations(variable, order)` preserves time/set metadata in this snapshot. These paths must not be conflated.
- NOISE_SEED controls estimator tie noise, not the default surrogate-order generator. Candidate validation uses explicit separately seeded donor maps and reloads each draw into a fresh calculator through the Step 7 exact-hour loader.

`jidt_runtime_surrogate_audit.csv` captures the actual arrays and tree eligibility INSIDE these surrogate calls. For an across-gap 46-hour separation, the CMI wrapper wrongly excludes the candidate while MI and optimized CMI single-ordering permit it. The 44/45-hour pairs remain excluded. This is runtime evidence, not just source inspection.

## Candidate nulls investigated

**Height MI:** test Ho independent of Hn. The candidate shifts Ho by exact hours on a complete time circle, permitting only rotations that preserve the entire retained timestamp mask, with a preselected minimum circular separation of 180 hours (four 45-hour windows). It preserves the observed values/count and, under the circular construction, within-series ordering and autocorrelation, except for the artificial wrap boundary. It assumes approximate stationarity and adequate decorrelation at the chosen shift; neither follows from the Theiler window alone. Synthetic gaps are repeated missing hours 5 and 6 every day, allowing legal multiples-of-24-hour shifts. For real irregular gaps, shifting compressed rows is not a physical-time shift, while shifting values together with their missingness masks and taking intersections changes the tested observations.

The two real timestamp masks have **zero admissible shifts** under this rule. An alternative inspected weekly-block rearrangement only swaps blocks with identical missingness patterns. It leaves all 6,867 Figure Eight Pools observations fixed and 9,688/10,522 Stockton observations fixed. It therefore fails to provide a meaningful full-record independence null. This audit uses timestamps only; it is not a propagation-lag sensitivity analysis.

**Period and direction CMI:** test Tp_o independent of Hn given Ho, or (Dx,Dy) jointly independent of Hn given Ho. The candidate implements [Runge (2018), Algorithm 1](https://proceedings.mlr.press/v84/runge18a.html): for each target, choose among its five nearest neighbours in scalar Ho, including itself; visit targets and donor lists in random order, prefer unused donors, and permit reuse when exhausted. This k_perm=5 is the surrogate neighbourhood, distinct from the unchanged estimator k=4. Direction columns always move together. The scheme approximately retains local source–Ho relationships, leaves the Hn–Ho sample unchanged, and disrupts source–Hn pairing. It does not guarantee a bijection: about 7.4% donor reuse and 21.7–21.8% unchanged source rows occurred in validation. Exact source marginals are therefore not guaranteed, and some original pairing remains. No claim of exact conditional exchangeability is made.

Pointwise local donors do **not** preserve source temporal dynamics. In autocorrelated synthetic conditional-null cases, mean one-hour period autocorrelation fell from 0.974 to 0.397; the direction cosine component fell from 0.932 to 0.330. Period–Ho correlation was approximately preserved (0.568 to 0.567). Small conditioning distances and preserved correlation do not prove preservation of the full conditional law. A Theiler window excludes close estimator neighbours; it does not repair a misspecified surrogate distribution.

## Synthetic validation

The validation includes independent and dependent Gaussian AR(1) series with rho=0 and 0.98, 5,000-hour burn-in, and the same periodic missing-hour mask. In conditional cases X=0.8Z+Ex and Y=0.8Z+Ey under the true conditional null, with independent innovation streams; under dependence, 0.8Ex is added to Y. Direction is (cos(1.2Z+Ex), sin(1.2Z+Ex)), so its components remain joint. MI uses independent Ex/Ey under the null and Y=0.8Ex+Ey under dependence.

Each scenario has 16 independent generated records, 1,232 retained observations and **20 candidate surrogates** per record: 192 synthetic tests and 4,032 actual Java estimator evaluations. Seed base is 20261101; each dataset starts from base + int(rho*1000)*100 + replicate, with the loop order and all donor maps saved. The estimator always retains the original Step 7 settings, including noise seed 20261031. Synthetic p-values use `(1 + count(null >= observed))/(20+1)`; their resolution is 1/21. These are candidate-method checks, not wave results.

'''+table(summary_show)+'''

Every observed and candidate-surrogate Java load verified the full intended time/set arrays and counts. Actual k=4 neighbour eligibility was checked at approximately 20 evenly spaced target rows per calculation. The underlying exact 44/45/46-hour boundary implementation was separately audited in Java. Thus computational timing integration passes, but this does not validate the statistical null.

These small checks show detection of known dependence and some null rejections; they do not establish calibrated type-I error. For example, direction nulls rejected in 2/16 independent and 2/16 autocorrelated records. With only 16 repetitions, this is insufficient to conclude either nominal calibration or statistically established inflation. The documented loss of temporal structure remains unresolved for the wave conditional tests. No wave pilot is warranted merely because the synthetic examples sometimes behave sensibly.

## Original estimates and status

'''+table(observed)+'''

Stockton's negative period CMI is preserved unchanged. No within-site significant finding, no Holm-adjusted finding, and no significant between-site difference is claimed. A difference in within-site p-values would not itself test a between-site contrast.

## Simplest defensible next options

1. **Retain Step 7 as descriptive results.** This satisfies the current observation/design constraints without reporting unsupported p-values.
2. **Approve a clearly separate, regular-segment or common-overlap testing analysis.** This can support temporal shifts or suitable block resampling, but changes the tested sample and requires recomputing its corresponding observed statistic. It must not be presented as a p-value for the unchanged full-record estimates.
3. **Develop a conditional time-series null model**, generating predictors conditional on offshore-height histories while modelling residual temporal dynamics. Validate null calibration with substantially more simulations and plausible persistence/missingness regimes before wave testing. This adds modelling assumptions; it has not been implemented here.

Simply increasing B to 199, applying Holm, adding the Theiler exclusion, or labelling global/local permutations as temporal surrogates would not resolve the null-model issues. A future approximate local-permutation analysis could only be labelled exploratory, with its limitations explicit; it would not satisfy a claim of validated time-series conditional significance at this stage.

## Files and reproduction

`wave_significance_status.csv`: six preserved estimates, null hypotheses, candidate methods/settings/seeds, B=0, missing surrogate summaries/p-values, and reasons for stopping. `validation/`: synthetic design, data, donor maps, every estimate, calibration summaries and Java logs. `wave_timestamp_mask_audit.json`: gap-pattern feasibility. `validation_gate.json`: explicit stop state. `preservation_checks.json`: hashes confirming original raw/cleaned files, autocorrelation and Step 7 artifacts are unchanged.

```
python3 src/validate_surrogate_methods.py
python3 src/report_surrogate_validation.py
python3 -m unittest discover -s tests
```

The validation command cannot launch wave significance testing. Eight automated tests pass, including the pre-existing actual Java timing test and new candidate-generator tests. No lag/k sensitivity, interpolation, extra outlier removal or research-design change was performed.
'''
    (OUT/'methodology.md').write_text(text)
    short = """# Step 8: validation complete; wave significance tests stopped

**The proposed null methods have unresolved validity problems.** Following the requested stop rule, no wave-data pilot or 199-surrogate analysis was run. `wave_significance_status.csv` retains all six original Step 7 values, including negative Stockton period CMI, with B=0 and p-values/adjusted p-values missing. No wave surrogate distributions exist; the plots here show synthetic validation only.

## What passed

The exact Step 7 jar/settings were verified. Every synthetic surrogate was loaded into a fresh Java calculator with the same elapsed-hour indices and set ID. All observations were retained, and actual nearest-neighbour searches respected the 45-hour exclusion. Eight automated tests passed. Hash checks confirm Step 7 estimates, datasets and autocorrelation artifacts are unchanged.

Runtime inspection of JIDT found that MI's optimized default path rearranges Hn while preserving custom time indices. The CMI `computeSignificance` wrapper shuffles variable 1 (or 2 if requested) but rebuilds compressed row-based time indices; its single-reordering optimized method preserves them. The across-gap 46-hour candidate was incorrectly excluded inside the CMI wrapper. Explicit timestamp-aware reloads avoid this computational problem.

## Why full testing stopped

**MI:** Large exact-hour circular shifts can preserve temporal ordering under stationarity/circular-boundary assumptions, but neither real missingness mask admits a shift preserving all retained observations. Swapping weekly blocks with identical gap patterns would leave all Figure Eight Pools observations and 92% of Stockton observations aligned. Compressing gaps or changing the matched sample would not test the requested unchanged full record.

**CMI:** A Runge (2018) Algorithm 1 candidate samples local donors among five neighbours in Ho, moving both direction components together. It approximately preserves source–Ho association, but donor reuse means it is not an exact permutation, and it does not preserve source autocorrelation. In autocorrelated conditional-null simulations, period one-hour ACF fell from 0.974 to 0.397, and direction-cosine ACF from 0.932 to 0.330. The Theiler window does not fix the resulting null-model mismatch.

The synthetic pilot used 20 surrogates for each of 192 generated tests spanning known independence/conditional independence/dependence, independent and AR(1) rho=0.98 processes, and missing hourly observations. These 16 repetitions per scenario showed useful dependence detection but are too few to establish calibrated type-I error. They neither prove validity nor demonstrate statistically established false-positive inflation. No wave significance claim follows.

## Defensible next options

1. Retain the six Step 7 estimates as descriptive results.
2. Define a separately labelled regular-segment or common-overlap testing analysis; this changes the tested observations and requires its own observed statistic.
3. Develop and calibrate a conditional time-series null model that preserves predictor–height associations and residual temporal dynamics, accepting the added modelling assumptions.

More surrogates or Holm correction cannot cure a misspecified null. There are no valid wave p-values to adjust, and no between-site significance claim is made.

See [detailed methodology and validation results](methodology.md), [six-test status CSV](wave_significance_status.csv), [runtime audit](jidt_runtime_surrogate_audit.csv), [synthetic summary](validation/synthetic_summary.csv), and [validation gate](validation_gate.json). Reproduce with `python3 src/validate_surrogate_methods.py`, then `python3 src/report_surrogate_validation.py`.
"""
    (OUT/'report.md').write_text(short)
    print('Saved stopped-analysis summary, methodology report, and explicitly synthetic plots.')


if __name__=='__main__':main()
