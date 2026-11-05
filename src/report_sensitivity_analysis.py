"""Render the prespecified Step 9 sensitivities; no p-values or setting selection."""
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
OUT=ROOT/'results/sensitivity_analysis'
SITES={'figure_eight_pools':'Figure Eight Pools','stockton':'Stockton'}
MEASURES={'height_mi':'Height MI','period_cmi':'Period CMI | height','direction_cmi':'Direction CMI | height'}
COLORS={'figure_eight_pools':'tab:blue','stockton':'tab:orange'}


def table(d):
    return '| '+' | '.join(d.columns)+' |\n|'+'|'.join(['---']*len(d.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in d.itertuples(index=False,name=None))+'\n'


def plot_panel(ax,data,measure,column,baseline):
    for site,label in SITES.items():
        rows=data.loc[data.site.eq(site)&data.measure.eq(measure)].sort_values(column)
        n=rows.sample_size
        nlabel=str(int(n.iloc[0])) if n.nunique()==1 else f'{int(n.min())}–{int(n.max())}'
        ax.plot(rows[column],rows.bits,'o-',color=COLORS[site],label=f'{label} (N={nlabel})')
        if baseline is not None:
            base=rows.loc[rows[column].eq(baseline)]
            ax.scatter(base[column],base.bits,s=85,facecolors='none',edgecolors='black',linewidths=.8,zorder=3)
    ax.axhline(0,color='grey',linewidth=.6)
    ax.set(title=MEASURES[measure],ylabel='Estimate (bits)')
    ax.legend(fontsize=8)


def main():
    d=pd.read_csv(OUT/'all_sensitivity_results.csv')
    if len(d)!=90:raise ValueError('Expected all 90 labelled result rows')
    gate=json.loads((OUT/'validation/acceptance.json').read_text())
    if not gate['passed']:raise RuntimeError('Integration failed')
    for factor,column,label,baseline in [('k','k','Nearest neighbours k',4),('theiler','theiler_hours','Theiler window (elapsed hours)',45)]:
        data=d.loc[d.analysis.eq(factor)]
        fig,axes=plt.subplots(1,3,figsize=(15,4.3))
        for ax,measure in zip(axes,MEASURES):
            plot_panel(ax,data,measure,column,baseline)
            ax.set(xlabel=label,xticks=sorted(data[column].unique()))
        fig.suptitle(f'{factor.title()} sensitivity: other settings fixed at Step 7 baseline; rings mark baseline')
        fig.tight_layout();fig.savefig(OUT/f'{factor}_sensitivity.png',dpi=160);plt.close(fig)
    data=d.loc[d.analysis.eq('lag')]
    fig,axes=plt.subplots(2,3,figsize=(15,8.5))
    for r,(cohort,label) in enumerate([('all_available','All available matches'),('common_source_timestamps','Common offshore source timestamps within each site')]):
        for ax,measure in zip(axes[r],MEASURES):
            plot_panel(ax,data.loc[data.cohort.eq(cohort)],measure,'lag_hours',None)
            ax.set(xlabel='Positive offshore-to-nearshore lag (hours)',xticks=[0,.5,1,2],title=MEASURES[measure]+'\n'+label)
    fig.suptitle('Lag sensitivity: k=4, exact W=45 h; common-time results are separate from original baseline')
    fig.tight_layout();fig.savefig(OUT/'lag_sensitivity.png',dpi=160);plt.close(fig)
    checks=[]
    for keys,group in d.groupby(['analysis','cohort','k','theiler_hours','lag_hours']):
        p=group.pivot(index='site',columns='measure',values='bits')
        f=p.loc['figure_eight_pools'];s=p.loc['stockton']
        checks.append(dict(zip(['analysis','cohort','k','theiler_hours','lag_hours'],keys),
                           height_mi_fep_greater=bool(f.height_mi>s.height_mi),
                           directional_cmi_stockton_greater=bool(s.direction_cmi>f.direction_cmi),
                           fep_height_bits=f.height_mi,stockton_height_bits=s.height_mi,
                           fep_direction_bits=f.direction_cmi,stockton_direction_bits=s.direction_cmi,
                           fep_period_bits=f.period_cmi,stockton_period_bits=s.period_cmi,
                           period_difference_fep_minus_stockton=f.period_cmi-s.period_cmi))
    checks=pd.DataFrame(checks);checks.to_csv(OUT/'qualitative_pattern_checks.csv',index=False)
    ranges=d.groupby(['site','analysis','cohort','measure'],as_index=False).agg(min_bits=('bits','min'),max_bits=('bits','max'))
    ranges.to_csv(OUT/'estimate_ranges.csv',index=False)
    counts=pd.read_csv(OUT/'lag_sample_counts.csv')
    display=counts[['site','cohort','lag_hours','sample_size']]
    overall=d.groupby(['site','measure'],as_index=False).agg(min_bits=('bits','min'),max_bits=('bits','max'))
    for col in ['min_bits','max_bits']:overall[col]=overall[col].map(lambda x:f'{x:.6f}')
    sign=d.loc[d.measure.eq('period_cmi'),['site','analysis','cohort','k','lag_hours','theiler_hours','bits']].copy()
    sign['estimate_sign']=np.sign(sign.bits).astype(int);sign.to_csv(OUT/'period_sign_checks.csv',index=False)
    text='''# Sensitivity analyses

The original six Step 7 estimates, cleaned data, raw data, autocorrelation results and Step 8 artifacts are unchanged. All six baselines were reproduced before sensitivity calculations: the largest difference is 2.22e-16 nats (serialization/floating-point precision; acceptance tolerance 1e-12). No significance tests or p-values were generated.

## Main findings

Across all 15 matched settings/cohorts, **height MI remains greater at Figure Eight Pools** and **direction CMI remains greater at Stockton**. Neither ordering reverses. Overall ranges across the prespecified analyses are:

'''+table(overall)+'''

Period CMI remains small in absolute magnitude (all estimates between -0.026519 and +0.030538 bits), but its sign is not stable:

- Stockton period CMI is negative at k=3/4/6, becoming +0.004362 bits at k=8. Across W=30/45/60 h it remains slightly negative.
- Figure Eight Pools period CMI is positive in the original-cleaned k/window analyses and all-available lag analysis. In the common-source cohort it changes from +0.017952 at zero lag to -0.001003 at 0.5 h, +0.005563 at 1 h and -0.018710 at 2 h.
- The common-source period ordering between sites reverses at 2 h, but by only about 0.000083 bits (Figure Eight Pools -0.018710 versus Stockton -0.018627). This is not a meaningful reversal of the main height/direction patterns or evidence of negative information.

Lag choice has more effect on directional CMI than the tested exclusion windows. At 2 h, all-available Figure Eight Pools directional CMI rises from 0.097002 to 0.125482 bits (about 29%), whereas Stockton falls from 0.231608 to 0.200080 bits (about 14%). Common-source comparisons retain this directional contrast: Figure Eight Pools spans 0.085080–0.114284 and Stockton 0.198232–0.234640 bits. Thus the cross-site ordering is stable, while the exact effect sizes depend on alignment. These percentages describe changes from zero lag, not inferential effect-size uncertainty.

W=30/45/60 h gives comparatively stable direction estimates (Figure Eight Pools 0.097002–0.098175; Stockton 0.229184–0.234277 bits). k sensitivity also retains the two main orderings. All negative finite-sample CMI estimates are saved without clipping; population CMI is nonnegative. No threshold was used to select a preferred setting or to classify significance.

## One-factor design and estimator

Each site is calculated separately with the same unmodified official JIDT source snapshot used by Step 7, commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456` and the same jar hash. All runs use KSG algorithm 1, NORMALISE=true, MAX_NORM, CPU, one worker thread, Gaussian noise 1e-8 after JIDT normalization and fixed NOISE_SEED=20261031. The source and response dimensions are (1,1) for height MI, (1,1|1) for period CMI and (2,1|1) for jointly encoded direction CMI.

Three separate analyses vary only:

- k=3,4,6,8, with W=45 h and zero lag, using identical original cleaned rows within each site.
- Physical lag=0,0.5,1,2 h, with k=4 and W=45 h, using freshly matched observations.
- W=30,45,60 h, with k=4 and zero lag, using identical original cleaned rows.

The 45-hour baseline remains primary. There is no exhaustive parameter grid, optimal-lag selection or replacement of primary results. The 90 result rows include baseline values under each analysis label; cached identical k/window calls are reused within a run. Every result records site, measure, N, k, physical lag, physical W, index units, nats/bits, estimator settings, source-time hash and JIDT provenance. `settings.json` records the fixed plan.

## Lag matching and physical interpretation

Positive tau means offshore Ho, Tp_o, Dx and Dy at t, with nearshore Hn at t+tau. Offshore archive TIME is UTC; nearshore Time is fixed AEST (UTC+10, no daylight saving). Original CSVs are read, numeric blanks coerced, both sources restricted to QC flag 1, and exact target timestamps joined one-to-one. Complete-variable rows are retained, with no interpolation, row shifting, trimming of valid extremes or additional QC rule.

The original nearshore half-hourly measurements are used, so the 0.5-hour case targets minute 30. All retained offshore source timestamps remain on clock hours; the Theiler index is therefore still in actual source hours and W=45 still means 45 hours. A separate Java test explicitly uses half-hour index ticks and W=90 ticks for 45 h, demonstrating correct conversion if source-grid resolution changes in a future analysis. A half-hour target delay alone does not require halving the source index unit.

These delays are a small exploratory alignment range at the available temporal resolution, not established travel times. Deployment readmes locate Figure Eight Pools at about (-34.1997,151.0506) and Stockton at (-32.9021,151.7988). Historical offshore locations in [CAWCR Technical Report 041, Appendix A](https://www.cawcr.gov.au/technical-reports/CTR_041.pdf) are approximately Port Kembla (-34.48,151.03) and Sydney (-33.77,151.42). These indicate separations of roughly 30 km and 100 km respectively (geographic approximations, not propagation paths or exact contemporaneous deployments). [Kinsela et al. (2024)](https://www.nature.com/articles/s41597-023-02865-x) identifies these buoy pairings and their contrasting nearshore settings. The points are not co-located or guaranteed to lie on one wave ray, particularly Sydney–Stockton. Consequently 0–2 h is reasonable as a limited exploratory timing check, but is not demonstrated to bracket physically plausible travel times for both pairs. A mechanistic delay would require wave direction, period and bathymetry/ray-path modelling; none is inferred from an MI maximum here.

## Sample composition

All-available results use each lag's complete raw-data matches; common-source results restrict each site's offshore timestamps to the intersection across all four delays. Thus Ho/Tp_o/Dx/Dy and source-time membership are held fixed across common-cohort lags while the target Hn changes. Common-source zero-lag results are a supplementary cohort, not the original baseline. Equal N alone is not the criterion: timestamp sets are explicitly compared. The two sites are never matched to each other.

'''+table(display)+'''

Common N is 6,316 for Figure Eight Pools and 10,307 for Stockton. The common-cohort shift in Figure Eight Pools zero-lag period CMI from the original 0.030538 to 0.017952 bits illustrates the effect of sample composition. Some all-available lagged matches can begin earlier than the original concurrent series, because a later valid nearshore observation can match an earlier offshore time; these are documented exact raw-data matches.

## Validation and files

Before sensitivity runs, all six Step 7 baselines and zero-lag raw-data rematches were checked against the original values and timestamps. Java integration tests cover hourly and half-hourly source grids with missing gaps, W=30/45/60 h, and k=3/4/6/8 at W=45. Twelve prespecified synthetic configurations each run MI and both CMI estimators. Actual joint-tree eligibility masks are checked for every point pair, marginal counts match the same mask, and actual k-nearest neighbours obey it. This includes boundary pairs immediately below, exactly at and immediately above each W, both within runs and across gaps. Java metadata validates all retained indices/counts/set IDs, with one shared set ID 0 per site and no cross-site calculator pooling. Direction dimensions are explicitly checked as (2,1,1). All fixed seed/normalization/norm/noise settings are read back from Java.

Eleven automated tests passed, including new raw half-hour/gap matching, real-data zero-lag equivalence, common timestamps and actual Java masks. `validation/acceptance.json`, `baseline_reproduction.csv`, `lag_matching.csv` and `java_integration.csv` record the gate evidence. `preservation_checks.json` confirms original data, Step 7/8 artifacts and preprocessing/autocorrelation code are unchanged.

- `all_sensitivity_results.csv`: all 90 labelled results in nats and bits.
- `k_sensitivity.csv`, `theiler_sensitivity.csv`, `lag_sensitivity.csv`: separate result tables.
- Matching PNG plots: separate panels for each information measure; lag plots also separate cohorts.
- `lag_sample_counts.csv`, `estimate_ranges.csv`, `qualitative_pattern_checks.csv`, `period_sign_checks.csv`: descriptive audits, with no p-values.
- `inputs/`: exact matched source/target timestamps and input tuples; `runs/`: raw JIDT estimates, actual time indices and logs.

Reproduce with `python3 src/sensitivity_analysis.py`, `python3 src/report_sensitivity_analysis.py`, and `python3 -m unittest discover -s tests`. Java/JDK and the already validated official JIDT build are required.

The site records cover different years and have different temporal coverage and sizes; common-source matching only controls composition within a site. These are descriptive robustness checks, not uncertainty intervals or tests of between-site differences. Step 8's unresolved surrogate-validity issues remain; stability across settings does not establish statistical significance or geomorphic causation.
'''
    (OUT/'report.md').write_text(text)
    print('Saved three sensitivity figures, comparison audits and report.')
    print(checks[['height_mi_fep_greater','directional_cmi_stockton_greater']].all().to_string())


if __name__=='__main__':main()
