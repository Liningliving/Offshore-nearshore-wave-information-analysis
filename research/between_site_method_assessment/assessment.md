# Focused assessment of between-site inference

## Decision

**Do not report wave-data confidence intervals or p-values with the current implementation.** One candidate between-site procedure was run, and it failed its pilot. Established subsampling frameworks exist, but I did not identify an already justified, practical drop-in procedure covering all three current fixed-k KSG MI/CMI contrasts, temporal dependence, irregular gaps and their finite-sample bias. This is not a claim that valid inference is impossible.

No new inference procedure, larger Monte Carlo study, JIDT calculation, wave confidence interval or wave p-value was implemented during this assessment. The code audit and diagnostics below use only saved pilot results. A larger simulation study should follow a specified defensible candidate, rather than being used to search for an interval correction that happens to pass.

## 1. What was actually attempted

Exactly **one** between-site interval construction was implemented:

- independent physical-time moving-window subsampling within each site;
- each window spans 25% of that site's record duration;
- 39 independent pairs of windows per simulated record pair;
- whole five-variable tuples are retained, without replacement within a draw;
- original time indices and gaps remain; no block concatenation or artificial time adjacency;
- separate site sample sizes are retained, not equalized;
- fixed Step 7 KSG1 settings and exact 45-hour Theiler exclusion are retained, with joint two-column direction;
- a separate-site root-N rescaling is used to construct a candidate error distribution, followed by quantile inversion.

Blocks can overlap between different resampling draws. That does not duplicate rows inside a single nearest-neighbour calculation. Natural measurement ties and resampling-created duplicate rows are distinct issues.

Ordinary bootstrap, moving/stationary bootstrap, site-label permutation, studentized subsampling, fixed-b calibration, bias-corrected inference and Holmes–Nemenman variance extrapolation **were not run as between-site tests**. Step 8 local permutations/circular shifts concerned within-site independence and are not additional attempted between-site procedures. `methods_inventory.csv` makes the distinction explicit.

### Exact interval formula

Let theta_j be a site-specific MI or CMI and n_j its full sample size, j=A (Figure Eight Pools), B (Stockton). For block draw b, m_jb is its actual retained count and theta_jb its estimate. Define s=+1 for height and s=-1 for period/direction:

\[
\widehat\Delta=s(\widehat\theta_A-\widehat\theta_B),\qquad
E_{jb}=\sqrt{m_{jb}/n_j}\,(\widehat\theta_{jb}-\widehat\theta_j),
\]

\[
D_b=s(E_{Ab}-E_{Bb}),\qquad
C_{.95}=\left[\widehat\Delta-Q_{.975}(D),\ \widehat\Delta-Q_{.025}(D)\right].
\]

The quantiles were NumPy's default linear-interpolation empirical quantiles over B=39 draws. There was **no studentization, explicit bias correction, long-run variance estimate or finite-block-fraction correction**. These were candidate intervals, not automatically valid 95% confidence intervals. The pilot did not construct empirical p-values; exclusion of zero was the implied two-sided test obtained by inverting the candidate interval.

## 2. Simulation settings and all coverage results

Each scenario had 12 independent record pairs, with 3,600 and 5,400 hourly source positions. Random missing observations and a longer outage were applied independently by site. Actual full sample counts ranged from 3,079–3,141 at A and 5,047–5,109 at B. Windows spanned 900 and 1,350 physical hours; actual block-count fractions ranged approximately 0.197–0.272. All three estimates used the same joint rows within a site/window.

Stationary Gaussian AR(1) latent components define Ho=3+Z, Tp_o=10+0.4Z+P, Hn=3+aZ+bP+cG+E and theta=2 arctan(G+0.3Z), with direction=(cos theta,sin theta). All latent components have variance one and independent innovation streams. Conditional on Z, the direction pair is an invertible encoding of G, giving analytical MI/CMI benchmarks. Fixed estimator noise 1e-8 is retained; the analytical benchmark is the underlying unperturbed distribution. The synthetic sampling mask is independent of the latent values. These are favorable continuous benchmarks, not a fitted model of the wave data.

Both equal-information scenarios use coefficients (a,b,c)=(1.2,0.3,0.4) at both sites. The unequal-information scenario changes B to (0.7,0.65,0.8). The true signed differences in that scenario are height +0.399081, period +0.111448 and direction +0.169183 bits. AR coefficients and results are below.

| Setting (AR coefficient A, B) | Measure | True difference (bits) | Coverage of candidate 95% interval | False positives under zero difference | Detection under known difference |
|---|---|---:|---:|---:|---:|
| Equal information (0.90, 0.90) | Height | 0 | 11/12 = 91.7% | 1/12 = 8.3% | — |
| Equal information (0.90, 0.90) | Period | 0 | 10/12 = 83.3% | 2/12 = 16.7% | — |
| Equal information (0.90, 0.90) | Direction | 0 | 8/12 = 66.7% | 4/12 = 33.3% | — |
| Equal information (0.80, 0.97) | Height | 0 | 8/12 = 66.7% | 4/12 = 33.3% | — |
| Equal information (0.80, 0.97) | Period | 0 | 9/12 = 75.0% | 3/12 = 25.0% | — |
| Equal information (0.80, 0.97) | Direction | 0 | 10/12 = 83.3% | 2/12 = 16.7% | — |
| Known difference (0.80, 0.97) | Height | +0.399081 | 10/12 = 83.3% | — | 12/12 = 100% |
| Known difference (0.80, 0.97) | Period | +0.111448 | 10/12 = 83.3% | — | 3/12 = 25.0% |
| Known difference (0.80, 0.97) | Direction | +0.169183 | 11/12 = 91.7% | — | 8/12 = 66.7% |

False-positive rates mean zero exclusions only in true-zero cases. In nonzero cases, zero exclusion is a detection rate, not a false-positive rate. Twelve experiments give very coarse and uncertain rate estimates; even 11/12 is not proof of 95% calibration. The initial screen rejected any scenario/measure with coverage below 80%. Passing that screen would only have permitted further validation, not immediate wave inference.

## 3. Why did intervals miss the truth?

The pilot does not uniquely identify a causal mechanism. It does rule out the explanation that successful Java execution alone makes the intervals valid: timestamp metadata and exclusion checks succeeded, but calibration did not. Re-examining the saved values gives concrete statistical diagnostics.

| Pilot setting and measure | SD of full contrast errors across the 12 simulations (bits) | Mean SD of candidate resampling errors (bits) | Ratio |
|---|---:|---:|---:|
| Equal information, different persistence: height | 0.136761 | 0.071583 | 0.523 |
| Equal information, same persistence: direction | 0.050213 | 0.034728 | 0.692 |

Thus the two 8/12 cases show substantial **underdispersion** of the candidate resampling distribution relative to variation between independent records. These are diagnostics estimated from only 12 simulations, not precise variance estimates.

Other failures are not simply narrow intervals. For period under equal information/different persistence, the mean full-contrast error is -0.041046 bits, while the candidate error distribution is centred at only -0.007057 bits. For direction in that setting, the mean full error is -0.051712 versus a candidate centre of +0.004222 bits. Such centring mismatches indicate finite-sample error/bias that a width-only adjustment would not necessarily fix. `pilot_error_diagnostics.csv` reports all settings separately.

Plausible contributors, not separately proven causes, are:

1. **A large block fraction without fixed-b calibration.** Traditional small-block asymptotics need blocks long enough to capture dependence but small relative to the full record. Here the duration fraction was fixed at 0.25. Even for an i.i.d. sample mean, centring a subset mean on the overlapping full mean reduces the scaled error variance by a factor 1-m/n. At m/n=0.25 this gives an SD factor sqrt(0.75)=0.866. That illustrates a problem; it is not a justified correction for these nonlinear gappy-record KSG estimates.
2. **An unverified root-N law and negligible-bias assumption.** Full-data and smaller-block KSG estimates can have different bias, particularly in CMI and when sample sizes differ. The Theiler window is a larger fraction of a small block. Circle-encoded direction, quantized wave data and tiny tie noise further limit direct application of smooth i.i.d. density-estimation results. None of this proves KSG point estimates invalid, but it prevents assuming that their interval scaling is correct.
3. **Different persistence and missingness.** Equal population MI/CMI does not imply equal sampling variability. Preserving a block's dependence/gaps is necessary but not sufficient to estimate full-record sampling error. Scaling only by retained counts cannot by itself establish the correct dependence-sensitive variance.
4. **Too few resamples for stable 95% endpoints.** With 39 draws, each 2.5% tail contains about one observation. Quantiles are noisy. More draws would reduce this Monte Carlo error, but would not automatically fix rate, bias or block-fraction problems.

Accordingly, “8/12 was caused by too-small blocks” or “multiply every interval width by 1.15” would be unsupported explanations. The failure is of this particular implementation at these tested sizes, not a proof that all subsampling methods must fail or that performance at the larger wave sample sizes must be identical.

## 4. Established methods assessed

### Independent-time-series block subsampling

[Politis and Romano (2010)](https://doi.org/10.1016/j.jmva.2008.11.005) provide an established framework for independent time-series samples. This is the most relevant general approach: retain joint blocks within each site and do not exchange labels or equalize full-record counts. However, its required limiting distribution/rate and block conditions must hold for the statistic. It is not a theorem automatically validating the particular root-N KSG MI/CMI implementation used here. The current gaps, bias and finite block fraction still need treatment.

**Assessment:** plausible research route, but not an accepted drop-in MSc implementation for all three existing contrasts. Choosing another block length without a rate/bias rationale and held-out calibration would be tuning rather than a validated method.

### KSG variance extrapolation without duplicate rows

[Holmes and Nemenman (2019)](https://doi.org/10.1103/PhysRevE.100.022404) show why naive bootstrap can distort KSG and develop subsampling-based variance/bias diagnostics. Their variance argument uses approximately 1/N scaling for sufficiently large independent contributions and non-overlapping subsets. Randomly partitioning autocorrelated hourly observations would not preserve temporal dependence; replacing their partitions with time blocks is a further adaptation. The paper is not a direct uncertainty result for this gappy-record CMI comparison, especially joint circular direction. Variance extrapolation also does not remove unknown bias merely by producing an SE.

**Assessment:** useful guidance and diagnostics, not a justified ready-made CI for the three current contrasts. This assessment does not reintroduce k sensitivity.

### Fixed-b calibration and studentized/self-normalized inference

[Shao and Politis (2013)](https://doi.org/10.1111/j.1467-9868.2012.01037.x) explicitly address dependence on the subsampling block fraction. Their framework relies on conditions such as an influence-function expansion and controlled remainders; applying the generic critical values to an arbitrary KSG/CMI statistic is not automatic. Related [coverage-bound results](https://doi.org/10.5705/ss.2014.185t) also warn that strong dependence and large block fractions can cause undercoverage. Studentization requires a reliable variance estimate; simply substituting one from the same failed block calculation is not validation.

**Assessment:** established methodology, but verifying/implementing it for this estimator, irregular sampling and direction encoding would exceed a simple correction and risks becoming a methodology-development project. It has not been tested here.

### Ordinary block bootstrap, smoothing and local-score standard errors

Moving/stationary with-replacement bootstrap preserves stretches of dependence but can duplicate original tuples, recreating the nearest-neighbour issue. Adding the existing 1e-8 tie noise does not make repeated observations independent information or justify that bootstrap. A smoothed/model-based bootstrap could generate new continuous observations, but requires a valid joint temporal/circular model or smoothing scheme and calibration. It is a different unvalidated procedure, not a simple fix.

Computing HAC or batch-mean standard errors from JIDT local information values is also not automatically valid: the local values share the same estimated neighbour graph. They cannot be assumed to be fixed independent influence-function scores solely because their average equals the reported MI/CMI. No such procedure was run.


## 5. Larger validation: decision and minimum standard

No new large simulation was launched because no revised practical method with an adequately specified justification was identified. The already rejected procedure should not be declared valid by increasing B, and repeatedly trying adjustments on the same 12 datasets would overfit the validation exercise. I am not claiming that the existing 12-run study provides a definitive impossibility result.

If formal inference remains mandatory, first fix an established candidate, its assumptions, treatment of bias, block rule and estimand with statistical supervision. Then use a substantially larger **independent, held-out** synthetic calibration, for example at least 500 record pairs per scenario and at least 399 resampling draws per pair. At 95% coverage, 500 independent experiments give a Monte Carlo standard error of about 0.98 percentage points. Those are planning numbers, not results.

Validation would need all three measures, zero and known nonzero contrasts, unequal actual-scale sample sizes, differing persistence, missing masks/gaps, nonlinear/rounded/circular examples and plausible distributional shapes. Report interval coverage and false-positive rate separately, with Monte Carlo uncertainty. Predefine acceptance rules that account for that uncertainty and the number of scenarios; preserve a held-out validation set after any tuning. Only after success should wave intervals or p-values be considered. Simulation success would support only the tested assumptions/regimes, not universal validity.

This is a substantial task rather than the practical minimum required for an MSc descriptive case study, so it is not my recommended next implementation under the current brief.

## 6. Practical MSc recommendation

Keep the central comparison explicit but state its inferential scope correctly:

> In the observed quality-filtered deployment records, height MI is 0.868023 bits greater at Figure Eight Pools, and directional CMI conditional on offshore height is 0.134605 bits greater at Stockton. The period contrast is -0.040520 bits under the Stockton-minus-Figure-Eight convention. These are descriptive contrasts between two case studies; uncertainty in the corresponding population differences has not been calibrated.

This answers “what differences do these two records show?” It does **not** formally reject a population zero-difference null, show general geomorphic effects or establish long-term site properties. Retain the existing limited lag/window checks as descriptive robustness, not sampling uncertainty. Do not use the range across sensitivity settings as a CI. Different years and environmental mixtures remain limitations, even if a future test becomes valid.

If the professor requires a formal test of the original population MI/CMI contrasts, that requirement remains unmet and should be discussed explicitly, rather than disguising a model-based test as the same question. The simplest defensible alternatives are an agreed descriptive two-case-study conclusion now, or a clearly separately defined inferential target / validated model. Neither additional variables nor an unannounced design change was introduced here.

## Audit and reproducibility

- `pilot_coverage_by_setting.csv`: all coverage counts, false-positive rates under true zero, and detection under known alternatives.
- `pilot_error_diagnostics.csv`: centring/spread diagnostics reconstructed from saved estimates, with no new resampling.
- `methods_inventory.csv`: what was actually run versus considered.
- `assessment_manifest.json`: original file hashes, unchanged-data confirmation and zero new estimator/simulation/wave-inference runs.
- Reproduce the numerical audit with `python3 src/assess_between_site_inference.py`.

All original Step 7 values, seeds, exact elapsed-hour exclusion, datasets and previous outputs are unchanged. No new wave confidence intervals or p-values have been created.
