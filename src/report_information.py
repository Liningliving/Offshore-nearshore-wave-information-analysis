"""Render the completed JIDT runs as plots and a reviewable analysis report."""
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
RESULTS=ROOT/'outputs/results'
FIGURES=ROOT/'outputs/figures'
LABELS={'mi_height':'Height MI','cmi_period':'Period CMI | height','cmi_direction':'Direction CMI | height'}
SITES={'figure_eight_pools':'Figure Eight Pools','stockton':'Stockton'}


def table(data):
    return '| '+' | '.join(map(str,data.columns))+' |\n|'+'|'.join(['---']*len(data.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in data.itertuples(index=False,name=None))+'\n'


def main():
    d=pd.read_csv(RESULTS/'information_results.csv')
    if len(d)!=96: raise ValueError(f'Expected 96 runs, found {len(d)}')
    primary=d.loc[d.variant.eq('primary')]
    baseline=primary.loc[primary.factor.eq('baseline')]
    baseline.to_csv(RESULTS/'primary_information_measures.csv',index=False)
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,(measure,label) in zip(axes,LABELS.items()):
        rows=baseline.loc[baseline.measure.eq(measure)]
        ax.bar([SITES[s] for s in rows.site],rows.bits,color=['tab:blue','tab:orange'])
        ax.axhline(0,color='black',linewidth=.6)
        ax.set(title=label,ylabel='Estimate (bits)')
        ax.tick_params(axis='x',labelrotation=12)
    fig.suptitle('JIDT KSG1: k=4, exclusion=45 retained rows, zero physical lag')
    fig.tight_layout(); fig.savefig(FIGURES/'primary_information_measures.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(14,11))
    for i,(measure,label) in enumerate(LABELS.items()):
        for j,(factor,column,xlabel) in enumerate([('k','k','Nearest neighbours k'),('window','window_rows','Exclusion (retained rows)'),('lag','lag_hours','Offshore-to-nearshore lag (hours)')]):
            ax=axes[i,j]
            for site,title in SITES.items():
                mask=primary.site.eq(site)&primary.measure.eq(measure)
                rows=primary.loc[mask & primary.factor.isin([factor,'baseline'])].sort_values(column)
                color='tab:blue' if site=='figure_eight_pools' else 'tab:orange'
                ax.plot(rows[column],rows.bits,'o-',color=color,label=title)
                if factor=='lag':
                    common=primary.loc[mask & primary.factor.eq('lag_common')].sort_values(column)
                    ax.plot(common[column],common.bits,'x--',color=color,label=title+' common times')
            ax.axhline(0,color='grey',linewidth=.5)
            ax.set(title=label,xlabel=xlabel,ylabel='Estimate (bits)')
            ax.legend(fontsize=7)
    fig.suptitle('One-factor sensitivities; other settings fixed at baseline')
    fig.tight_layout();fig.savefig(FIGURES/'information_sensitivity.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(14,8))
    for i,(site,title) in enumerate(SITES.items()):
        for j,(measure,label) in enumerate(LABELS.items()):
            row=baseline.loc[baseline.site.eq(site)&baseline.measure.eq(measure)].iloc[0]
            values=pd.read_csv(ROOT/row.output_file)
            null=values.loc[values.kind.eq('surrogate'),'bits']
            ax=axes[i,j]; ax.hist(null,bins=25,alpha=.7)
            ax.axvline(row.bits,color='tab:red',label=f'Observed {row.bits:.4f}')
            ax.set(title=title+': '+label,xlabel='Bits',ylabel='Surrogates')
            ax.legend(fontsize=8)
    fig.suptitle('Surrogate diagnostics: MI unrestricted; CMI offshore-height-stratified')
    fig.tight_layout();fig.savefig(FIGURES/'information_surrogates.png',dpi=160);plt.close(fig)
    display=baseline[['site','measure','n','nats','bits','p_plus_one']].copy()
    for column in ['nats','bits']: display[column]=display[column].map(lambda x:f'{x:.6f}')
    display.p_plus_one=display.p_plus_one.map(lambda x:f'{x:.3f}')
    lag=primary.loc[primary.measure.eq('mi_height') & primary.factor.isin(['baseline','lag','lag_common']),['site','cohort','lag_hours','n']].sort_values(['site','cohort','lag_hours'])
    audit=pd.read_csv(RESULTS/'information_exclusion_audit.csv')
    audit=audit.loc[audit.lag_hours.eq(0)&audit.cohort.eq('available')&audit.k.eq(4)&audit.window_rows.eq(45)]
    audit=audit[['site','physical_pairs_within_window','row_index_excluded_pairs','extra_pairs_excluded_across_gaps','extra_fraction_of_index_exclusions']]
    audit.extra_fraction_of_index_exclusions=audit.extra_fraction_of_index_exclusions.map(lambda x:f'{100*x:.2f}%')
    reference=d.loc[d.factor.eq('baseline'),['site','measure','variant','conditioning_bins','surrogates','p_plus_one','surrogate_mean_bits']].copy()
    reference.surrogate_mean_bits=reference.surrogate_mean_bits.map(lambda x:f'{x:.6f}')
    text='''# JIDT primary measures, surrogate diagnostics and sensitivity analysis

## Primary results

All estimates use the user's JIDT 1.6.1 jar through its Java API, not GUI automation. The jar and its accompanying version-specific source were inspected. Python prepares observations and invokes the compiled Java runner. No GUI-control facility is available in this session.

'''+table(display)+'''
`p_plus_one` is an upper-tail Monte Carlo diagnostic, qualified below. Negative finite-sample estimates are retained rather than clipped; true MI/CMI cannot be negative. Heights remain matching time-domain WHTH/Hsig, not spectral Hm0.

## Consistent estimator settings

- JIDT `MutualInfoCalculatorMultiVariateKraskov1` and `ConditionalMutualInfoCalculatorMultiVariateKraskov1` (algorithm 1).
- Baseline k=4; CPU, four threads; max norm (JIDT default). Already aligned observations, MI TIME_DIFF=0.
- Each input column is standardized to zero mean and sample standard deviation 1 within its dataset/cohort. JIDT NORMALISE=false to avoid a second normalization.
- Tie-breaking Gaussian noise of standard deviation 1e-8 is added externally in standardized units using NumPy default_rng seed 20261030. JIDT NOISE_LEVEL_TO_ADD=0. The same prepared file is reused across k/window changes.
- All surrogate orders use Java Random seed 20261030. Reproducibility settings, column means/scales, input hashes and the jar SHA-256 are in information_settings.json.
- Raw estimator units are nats; bits = nats / ln(2). Both are saved. Direction uses a single n-by-2 predictor [Dx, Dy]; both components are permuted together.

## Theiler exclusion: version-specific correction

The previous source review used current upstream JIDT, whose elapsed-time-tracking API is absent from this 1.6.1 jar. Version 1.6.1 also rejects dynamic exclusion across multiple observation sets. Therefore the new Java runner uses one chronologically ordered set and DYN_CORR_EXCL=45 **retained row indices**, not an exact 45-hour exclusion.

Every retained offshore timestamp lies on an hourly grid, so row distance is never larger than elapsed hours. Excluding 45 rows therefore excludes every observed pair within 45 hours, plus some pairs farther apart across gaps. This is conservative with respect to excluding temporally close observations, but it is not guaranteed to be conservative for the MI/CMI value or a p-value. The following unordered-pair counts quantify the discrepancy:

'''+table(audit)+'''
No gap is filled or interpreted as a one-hour physical interval. A version supporting actual observation time IDs would be required to implement the exact physical-time exclusion with the earlier helper. `src/jidt_timing.py` remains a helper for that newer API and is not called by this runner. The 0, 23, 45 and 90 sensitivity windows below have these same retained-row units.

## Surrogate tests and their interpretation

A pilot used 9 surrogates per primary measure, followed by 199 per primary final diagnostic (minimum reported p = 0.005). All null values are saved, and p = (1 + number of null estimates >= observed)/(B+1), avoiding zero Monte Carlo p-values. JIDT's empirical distribution uses count/B internally; the report intentionally recomputes the plus-one value.

For MI, JIDT permutes offshore Ho across observation indices, retaining Hn. This asks whether the observed height association exceeds an unrestricted-permutation reference.

For CMI, JIDT's default `computeSignificance` permutes variable 1 (or variable 2 when requested) while holding the other variable and Ho fixed. A default unrestricted shuffle destroys the predictor's dependence on Ho. It is not automatically a valid test of conditional independence.

Here, explicit permutation orders are supplied to JIDT `computeSignificance(1, orders)`. Predictor rows are shuffled only within 50 rank-based equal-count Ho groups, holding Hn and Ho fixed. For direction the same row permutation moves Dx and Dy jointly. This approximately preserves predictor-height dependence and breaks predictor-nearshore pairing locally in height. It conditions on coarse height groups, not exactly on continuous Ho. Group spans vary, especially in the tails, so residual confounding and null distortion remain possible. References use 25 and 100 groups and an unrestricted shuffle, each with 99 surrogates.

All these shuffles disrupt temporal autocorrelation; the Theiler window does not repair this null-model limitation. Hence these p-values are exploratory surrogate diagnostics, not confirmatory tests of conditional independence or autocorrelation-robust significance. No multiplicity-adjusted family-wide significance claims are made. Sensitivity runs report point estimates, not additional surrogate p-values. A stronger inferential claim would require a validated conditional resampling model that also handles temporal dependence.

'''+table(reference)+'''
## Sensitivities and timestamp alignment

Change one factor at a time: k=3,4,6,8 with window=45; window=0,23,45,90 with k=4; and positive physical lag=0,0.5,1,2 hours with k=4/window=45. Positive lag means offshore at t is matched to nearshore Hn at t+lag. Original half-hourly nearshore observations and offshore records are QC-filtered and rematched on actual timestamps for every lag, not shifted by retained row position.

The short lag set brackets exploratory sub-hour to two-hour alignment differences at the native nearshore resolution; these are not estimated propagation times. In particular, Sydney and Stockton are spatially separated reference locations and need not represent a direct wave propagation path. No lag was selected to maximize or report a corrected primary significance result.

Available-timestamp analyses use every complete match at each lag. Common-timestamp analyses restrict each site to offshore timestamps available at ALL four lags, holding sample membership and N fixed across lags. They keep all three measures on the same rows. Sample counts are:

'''+table(lag)+'''
All 96 estimates/reference runs and their sample counts are in information_results.csv. Detailed surrogate draws are in information_runs/, and prepared standardized inputs plus paired offshore/nearshore timestamps are in information_inputs/.

## Findings and limits

Offshore-height MI is consistently larger at Figure Eight Pools, and directional CMI is consistently larger at Stockton, across the tested k, exclusion settings and lags, including common-timestamp lag comparisons. Those patterns support the proposed height and direction contrasts descriptively.

The proposed larger period contribution at Stockton is not supported: its estimate is close to zero and slightly negative at baseline, and period estimates change sign in some k/lag settings. Figure Eight Pools has a small positive baseline period estimate, but common-timestamp lag estimates also cross zero, so this contribution should be described as weak and sensitive.

Removing exclusion raises period CMI from 0.028574 to 0.121373 bits at Figure Eight Pools and from -0.007730 to 0.154348 bits at Stockton. Direction CMI also rises. This illustrates why conclusions should use the exclusion and its sensitivity checks rather than the no-exclusion estimates alone. Positive exclusion windows give much closer directional estimates.

The two sites have unequal samples and different observation years. No uncertainty interval for the between-site difference has been estimated. The observed contrasts are site-specific associations, not evidence that geomorphology alone caused them. Period and direction CMI each condition only on Ho and may overlap; their values must not be added as independent contributions.

## Reproduction and validation

```
python3 src/information_analysis.py --pilot
python3 src/information_analysis.py --surrogates 199
python3 src/report_information.py
python3 -m unittest discover -s tests
```

Java and javac must be available. `--jar` can override the default path. No JPype installation is needed. Fingerprinted caching on subsequent runs checks the command, Java source, input and jar hashes before reusing a result.

Seven automated tests passed, including real JIDT runtime integration with a Gaussian MI of known theoretical value, conditional-confounding and direct-dependence examples, deterministic repeated surrogate runs, bit conversion, physical half-hour timestamp alignment, conservative-exclusion counts, and the earlier ACF/timing checks. The Java integration tests use the local jar. No input observations are interpolated or removed for being extreme; all two-site definitions and preprocessing rules are preserved.

Version-specific sources inspected locally:

- `jidt-1.6.1/java/source/infodynamics/measures/continuous/kraskov/MutualInfoCalculatorMultiVariateKraskov.java`: exclusion properties and multiple-set restriction.
- `jidt-1.6.1/java/source/infodynamics/measures/continuous/kraskov/ConditionalMutualInfoCalculatorMultiVariateKraskov.java`: conditional estimator and exclusion properties.
- `jidt-1.6.1/java/source/infodynamics/measures/continuous/MutualInfoMultiVariateCommon.java` and `ConditionalMutualInfoMultiVariateCommon.java`: default surrogate variable and supplied permutation orders.
- `jidt-1.6.1/java/source/infodynamics/utils/EmpiricalMeasurementDistribution.java`: empirical tail calculation.
'''
    (RESULTS/'information_analysis_report.md').write_text(text)
    print('Saved primary table, three figures and information_analysis_report.md')


if __name__=='__main__': main()
