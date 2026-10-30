# JIDT primary measures, surrogate diagnostics and sensitivity analysis

## Primary results

All estimates use the user's JIDT 1.6.1 jar through its Java API, not GUI automation. The jar and its accompanying version-specific source were inspected. Python prepares observations and invokes the compiled Java runner. No GUI-control facility is available in this session.

| site | measure | n | nats | bits | p_plus_one |
|---|---|---|---|---|---|
| figure_eight_pools | mi_height | 6867 | 1.077073 | 1.553889 | 0.005 |
| figure_eight_pools | cmi_period | 6867 | 0.019806 | 0.028574 | 0.010 |
| figure_eight_pools | cmi_direction | 6867 | 0.068990 | 0.099532 | 0.005 |
| stockton | mi_height | 10522 | 0.470016 | 0.678090 | 0.005 |
| stockton | cmi_period | 10522 | -0.005358 | -0.007730 | 0.800 |
| stockton | cmi_direction | 10522 | 0.161467 | 0.232948 | 0.005 |

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

| site | physical_pairs_within_window | row_index_excluded_pairs | extra_pairs_excluded_across_gaps | extra_fraction_of_index_exclusions |
|---|---|---|---|---|
| figure_eight_pools | 273730 | 307980 | 34250 | 11.12% |
| stockton | 439621 | 472455 | 32834 | 6.95% |

No gap is filled or interpreted as a one-hour physical interval. A version supporting actual observation time IDs would be required to implement the exact physical-time exclusion with the earlier helper. `src/jidt_timing.py` remains a helper for that newer API and is not called by this runner. The 0, 23, 45 and 90 sensitivity windows below have these same retained-row units.

## Surrogate tests and their interpretation

A pilot used 9 surrogates per primary measure, followed by 199 per primary final diagnostic (minimum reported p = 0.005). All null values are saved, and p = (1 + number of null estimates >= observed)/(B+1), avoiding zero Monte Carlo p-values. JIDT's empirical distribution uses count/B internally; the report intentionally recomputes the plus-one value.

For MI, JIDT permutes offshore Ho across observation indices, retaining Hn. This asks whether the observed height association exceeds an unrestricted-permutation reference.

For CMI, JIDT's default `computeSignificance` permutes variable 1 (or variable 2 when requested) while holding the other variable and Ho fixed. A default unrestricted shuffle destroys the predictor's dependence on Ho. It is not automatically a valid test of conditional independence.

Here, explicit permutation orders are supplied to JIDT `computeSignificance(1, orders)`. Predictor rows are shuffled only within 50 rank-based equal-count Ho groups, holding Hn and Ho fixed. For direction the same row permutation moves Dx and Dy jointly. This approximately preserves predictor-height dependence and breaks predictor-nearshore pairing locally in height. It conditions on coarse height groups, not exactly on continuous Ho. Group spans vary, especially in the tails, so residual confounding and null distortion remain possible. References use 25 and 100 groups and an unrestricted shuffle, each with 99 surrogates.

All these shuffles disrupt temporal autocorrelation; the Theiler window does not repair this null-model limitation. Hence these p-values are exploratory surrogate diagnostics, not confirmatory tests of conditional independence or autocorrelation-robust significance. No multiplicity-adjusted family-wide significance claims are made. Sensitivity runs report point estimates, not additional surrogate p-values. A stronger inferential claim would require a validated conditional resampling model that also handles temporal dependence.

| site | measure | variant | conditioning_bins | surrogates | p_plus_one | surrogate_mean_bits |
|---|---|---|---|---|---|---|
| figure_eight_pools | mi_height | primary | 0 | 199 | 0.005 | 0.019246 |
| figure_eight_pools | cmi_period | primary | 50 | 199 | 0.01 | -0.001274 |
| figure_eight_pools | cmi_period | unrestricted_reference | 0 | 99 | 0.01 | -0.000664 |
| figure_eight_pools | cmi_period | conditional_bins25 | 25 | 99 | 0.01 | -0.001158 |
| figure_eight_pools | cmi_period | conditional_bins100 | 100 | 99 | 0.01 | -0.002469 |
| figure_eight_pools | cmi_direction | primary | 50 | 199 | 0.005 | -0.002101 |
| figure_eight_pools | cmi_direction | unrestricted_reference | 0 | 99 | 0.01 | -0.001548 |
| figure_eight_pools | cmi_direction | conditional_bins25 | 25 | 99 | 0.01 | -0.002142 |
| figure_eight_pools | cmi_direction | conditional_bins100 | 100 | 99 | 0.01 | -0.002250 |
| stockton | mi_height | primary | 0 | 199 | 0.005 | 0.012967 |
| stockton | cmi_period | primary | 50 | 199 | 0.8 | -0.000950 |
| stockton | cmi_period | unrestricted_reference | 0 | 99 | 0.83 | 0.000773 |
| stockton | cmi_period | conditional_bins25 | 25 | 99 | 0.83 | -0.000187 |
| stockton | cmi_period | conditional_bins100 | 100 | 99 | 0.87 | -0.000424 |
| stockton | cmi_direction | primary | 50 | 199 | 0.005 | -0.000439 |
| stockton | cmi_direction | unrestricted_reference | 0 | 99 | 0.01 | -0.000512 |
| stockton | cmi_direction | conditional_bins25 | 25 | 99 | 0.01 | 0.001139 |
| stockton | cmi_direction | conditional_bins100 | 100 | 99 | 0.01 | -0.000992 |

## Sensitivities and timestamp alignment

Change one factor at a time: k=3,4,6,8 with window=45; window=0,23,45,90 with k=4; and positive physical lag=0,0.5,1,2 hours with k=4/window=45. Positive lag means offshore at t is matched to nearshore Hn at t+lag. Original half-hourly nearshore observations and offshore records are QC-filtered and rematched on actual timestamps for every lag, not shifted by retained row position.

The short lag set brackets exploratory sub-hour to two-hour alignment differences at the native nearshore resolution; these are not estimated propagation times. In particular, Sydney and Stockton are spatially separated reference locations and need not represent a direct wave propagation path. No lag was selected to maximize or report a corrected primary significance result.

Available-timestamp analyses use every complete match at each lag. Common-timestamp analyses restrict each site to offshore timestamps available at ALL four lags, holding sample membership and N fixed across lags. They keep all three measures on the same rows. Sample counts are:

| site | cohort | lag_hours | n |
|---|---|---|---|
| figure_eight_pools | available | 0.0 | 6867 |
| figure_eight_pools | available | 0.5 | 6873 |
| figure_eight_pools | available | 1.0 | 6863 |
| figure_eight_pools | available | 2.0 | 6863 |
| figure_eight_pools | common | 0.0 | 6316 |
| figure_eight_pools | common | 0.5 | 6316 |
| figure_eight_pools | common | 1.0 | 6316 |
| figure_eight_pools | common | 2.0 | 6316 |
| stockton | available | 0.0 | 10522 |
| stockton | available | 0.5 | 10524 |
| stockton | available | 1.0 | 10521 |
| stockton | available | 2.0 | 10522 |
| stockton | common | 0.0 | 10307 |
| stockton | common | 0.5 | 10307 |
| stockton | common | 1.0 | 10307 |
| stockton | common | 2.0 | 10307 |

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
