# Technical workflow and reproducibility

This document explains implementation and verification. Scientific findings and interpretation belong in the [scientific report](../final_scientific_report.md); analysis scope and limitations are summarized in the [root README](../README.md#limitations). The former primary-information report's unique technical details are consolidated here; its duplicate results table and scientific discussion are omitted.

## 1. Environment and pinned JIDT build

Run commands from the project root using the existing virtual environment. Base dependencies are [requirements.txt](../requirements.txt); [config/requirements-report.txt](../config/requirements-report.txt) adds Word-report support. A local JDK is required for estimator/integration commands. The saved analysis used OpenJDK/javac 21.0.12.1 and official JIDT source commit **1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456** (3 August 2026). The build label remains 1.6.1; the commit and jar hash distinguish this source snapshot from the older release jar.

The unmodified official source is in tools/jidt/source/; the compiled jar and provenance are in tools/jidt/build/. The original build compiled 250 source files with `--release 8`. See [build_manifest.json](../tools/jidt/build/build_manifest.json) and [build.log](../tools/jidt/build/build.log). The external original 1.6.1 setup was preserved as a fallback, but the recorded primary estimates use the pinned official snapshot.

If the ignored source checkout is absent, obtain and pin it before running the verification-dependent estimators:

```sh
git clone https://github.com/jlizier/jidt.git tools/jidt/source
git -C tools/jidt/source checkout 1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456
```

Skip cloning if the checkout is already present. Rebuild only if necessary with `.venv/bin/python src/build_jidt_official.py`. The runner checks the jar hash, source commit and clean upstream source even when a jar already exists. A failed provenance/integration check stops estimation. No estimator algorithm was patched.

## 2. Pipeline and commands

### Rebuild scopes

| Scope | Required inputs | What runs |
|---|---|---|
| Report only | Saved numerical results/metadata, existing selected figures and manuscript template | `consolidate_final_report.py`; no Java or estimation |
| Figures and report | Same saved analysis inputs; figure script also reads cleaned observations and saved preprocessing correlations | `make_presentation_figures.py`, then `consolidate_final_report.py`; no JIDT |
| Numerical rerun | Raw data, Python environment, local JDK and pinned JIDT source/build | Preprocessing, ACF, primary estimators and sensitivity stages |

A report-only rebuild was verified in temporary storage using the current saved inputs and installed dependencies. It produced Markdown, Word and a manifest without changing the existing science artifacts.

A fresh Git clone already contains the saved analysis products needed for the first two scopes; the ignored virtual environment must be recreated. Installing config/requirements-report.txt also installs the base requirements through its relative include. Run all commands from the repository root.

**A numerical rerun is not a clean-room rebuild of every repository artifact.** The comparison table, verified dataset description, manuscript template and verified-source hashes are retained inputs; current scripts consume them rather than reconstructing all of them from scratch. Historical inference reports also document earlier runs. Do not delete all results/research folders and expect report assembly to recreate them. Regenerated CSV metadata, library versions or JIDT build hashes can differ even when estimates are close; verification gates deliberately stop on such differences. Review a numerical rerun separately instead of bypassing the reference checks.


Current results are already saved. The commands below regenerate their individual products; they are not a single automatic whole-repository build.

| Purpose | Command | Main product |
|---|---|---|
| Preprocess original observations | `.venv/bin/python src/preprocess.py` | data/processed/, results/preprocessing/ |
| Timestamp-aware autocorrelation | `.venv/bin/python src/autocorrelation.py` | results/preprocessing/ and exploratory figures |
| Six primary MI/CMI estimates | `.venv/bin/python src/primary_information.py` | results/primary_information/ |
| Java timing checks only | `.venv/bin/python src/primary_information.py --integration-only` | Primary integration evidence |
| Historical surrogate-method validation | `.venv/bin/python src/validate_surrogate_methods.py` | research/surrogate_validation/ |
| Summarize that validation | `.venv/bin/python src/report_surrogate_validation.py` | Same directory; wave testing remains stopped |
| Reproduce historical sensitivity calculations | `.venv/bin/python src/sensitivity_analysis.py` | results/sensitivity_analysis/ |
| Summarize saved sensitivity results | `.venv/bin/python src/report_sensitivity_analysis.py` | Same directory |
| Generate selected presentation figures | `.venv/bin/python src/make_presentation_figures.py` | deliverables/figures/ |
| Assemble the scientific report | `.venv/bin/python src/consolidate_final_report.py` | Root Markdown/Word reports; supporting copies and manifest in deliverables/ |
| Check implementation | `.venv/bin/python -m unittest discover -s tests` | Temporary numerical/Java test evidence |

For a deliberate numerical rerun, after obtaining/verifying the pinned JIDT checkout, the main calculation order is:

```sh
# Only rebuild the official jar if necessary:
.venv/bin/python src/build_jidt_official.py
.venv/bin/python src/preprocess.py
.venv/bin/python src/autocorrelation.py
.venv/bin/python src/primary_information.py
.venv/bin/python src/sensitivity_analysis.py
.venv/bin/python src/report_sensitivity_analysis.py
```

These commands recompute the numerical stages, not the versioned comparison/description inputs. Proceed to figure/report assembly only after reviewing the resulting outputs and compatibility checks. Surrogate-method and failed subsampling studies are separate historical investigations, not prerequisites to rerun automatically or routes to new significance claims.

Preprocessing uses original QC flags, complete concurrent tuples, nonnegative heights and positive periods, without interpolation or removal of valid extremes. Offshore TIME is UTC; nearshore Time is fixed AEST (UTC+10), converted to UTC. Data definitions, sampling and physical interpretation are documented in the scientific report. Their implementation audit is [preprocessing_audit.json](../results/preprocessing/preprocessing_audit.json).

## 3. Primary calculators and settings

Each site uses separate CPU JIDT calculators. The Python runner launches compiled Java adapters through subprocess; it does not require JPype. Shared application settings are in src/java/SharedEstimatorSettings.java and timestamp loading in src/java/ElapsedHourLoader.java.

| Measure | Calculator | Predictor / response / condition dimensions |
|---|---|---|
| Height MI | MutualInfoCalculatorMultiVariateKraskov1 | (1,1,0) |
| Period CMI conditioned on offshore height | ConditionalMutualInfoCalculatorMultiVariateKraskov1 | (1,1,1) |
| Joint-direction CMI conditioned on offshore height | ConditionalMutualInfoCalculatorMultiVariateKraskov1 | (2,1,1) |

All primary runs use k=4, NORMALISE=true, NORM_TYPE=MAX_NORM, DYN_CORR_EXCL=45 exact elapsed hours, USE_GPU=false and one worker thread. MI TIME_DIFF=0 because supplied tuples are concurrent. This property is separate from both temporal exclusion and the physical lag used in sensitivity calculations. Direction is one predictor array containing Dx and Dy; separate cosine/sine information values are not summed. Negative finite-sample CMI estimates remain unchanged.

JIDT returns nats; bits=nats/ln(2). The [primary summary CSV](../results/primary_information/primary_information_summary.csv) stores both units, dimensions, settings, Java/JIDT versions, source commit/jar hash, noise stage, input/timestamp hashes, sample counts and retained timestamp limits. It is the authoritative full-precision table; the report supplies its interpretation.

## 4. Rounded observations and reproducible tie treatment

Saved exact-value counts show substantial measurement ties. Figure Eight Pools has 51 distinct Tp_o values and 190 direction pairs among 6,867 observations; Stockton has 52 and 178 among 10,522. Duplicate height pairs beyond the first occurrence number 272 and 358. No complete five-variable tuple is duplicated. [ties_audit.csv](../results/primary_information/ties_audit.csv) distinguishes distinct values, all rows in repeated groups and duplicates beyond the first. These counts describe stored values, without additional rounding.

Every calculator explicitly uses JIDT Gaussian noise with NOISE_LEVEL_TO_ADD=1e−8 and NOISE_SEED=20261031. Official code adds noise **after per-component normalization**; no external jitter or normalization is applied and no cleaned measurement is overwritten. The small level is negligible relative to measurement resolution, but continuous-estimator approximation and finite-sample bias remain limitations. Different calculator dimensions consume the seeded random stream differently; reproducibility does not mean identical perturbations across all measures.

## 5. Exact elapsed-hour exclusion across gaps

The established common 45-hour baseline comes from the [timestamp-aware autocorrelation analysis](../results/preprocessing/autocorrelation_report.md), not a new calculation here. Existing helpers hourly_indices and timed_blocks validate timestamps and identify contiguous hourly segments. The Java loader uses addObservationsTrackObservationIDs with each segment's original elapsed-hour start and the **same observation-set ID 0** within one site's time series. Separate sites are not combined in one calculator. Missing hours remain gaps; no padded observations enter JIDT.

After finalization, actual observationTimePoints, observationSetIndices and retained counts are checked against the intended arrays. The saved site records contain 378 and 265 hourly segments. Every observed timestamp is checked for all three calculators. This is elapsed-time exclusion, rather than retained-row separation.

### Existing runtime evidence

- Java property readbacks and synthetic subclass checks verify active k, exclusion, normalization, norm, noise, seed and dimensions.
- The integration dataset contains 241 observations across multiple hourly runs, gaps and a singleton. All observations and actual indices are retained.
- Across all 28,920 unordered pairs per calculator, actual joint-tree eligibility matches absolute elapsed-hour separation >45, with zero mismatches.
- Joint and marginal searches and actual k=4 neighbour selections obey the same exclusion.
- Separation of 44 or 45 hours is excluded and 46 hours is eligible, both within segments and across gaps; a 71-hour long-gap pair is eligible.
- A negative control uses different set IDs and permits an 11-hour cross-gap neighbour, demonstrating why separate segments must share one set ID.
- MI and both CMI calculations run, and joint-direction dimensions are verified. Seeded repeats produce identical normalized/noised predictor arrays and synthetic outputs.
- Original integration testing passed all five checks recorded at that stage, including the actual Java test; Python-only helper tests were not treated as Java proof.

Inspect [acceptance.json](../results/primary_information/integration/acceptance.json), [java_results.json](../results/primary_information/integration/java_results.json), [observation_indices.csv](../results/primary_information/integration/observation_indices.csv) and [pair_eligibility.csv](../results/primary_information/integration/pair_eligibility.csv). The site-specific *_java_indices.csv, *_segments.csv and *_retained_timestamps.csv files in results/primary_information/ retain the real-data loading evidence. [preservation_checks.json](../results/primary_information/preservation_checks.json) records the original run's protected inputs/code/fallback-jar hashes. Such historical hashes describe the code and paths at execution time.

## 6. Sensitivity and inferential boundaries

The final report uses the existing lag and Theiler-window results with k=4. Positive lag compares offshore(t) with nearshore(t+τ) by timestamp rematching, not row offsets. Common source timestamps are defined separately within each site and distinguished from all-available matches. The historical sensitivity runner reproduces its original full numerical set, including retained neighbourhood checks; those k checks are excluded from the final main report and selected figures. See [sample counts](../results/sensitivity_analysis/lag_sample_counts.csv) and [saved sensitivity results](../results/sensitivity_analysis/all_sensitivity_results.csv).

The failed whole-record subsampling evidence and [methodological assessment](../research/between_site_method_assessment/assessment.md) explain the between-site inference limitation. Re-running a failed pilot does not authorize significance claims. Within-site surrogate validity is a separate unresolved issue, described in its [validation report](../research/surrogate_validation/report.md). Correct Java integration and stable numerical orderings do not establish calibrated wave-data p-values or confidence intervals.

Figures read saved results and preprocessing correlations; they do not calculate new information measures. The scientific report is assembled from docs/templates/final_report.md with tables filled from saved CSVs. Historical execution paths, including links to the consolidated documents, resolve through src/artifact_paths.py and config/legacy_paths.json.

## 7. Submission and disclosure notes

The [original PDF](project_proposal.pdf) is a seven-page proposal, not a full marking rubric. Verify institution-specific length, format, references and AI-disclosure requirements against the actual assessment instructions. AI assistance extended beyond the proposal's brainstorming/wording description to implementation, methodological evaluation and report drafting; any declaration should reflect actual use. No signed author declaration or independent author verification is fabricated by the report-generation code.
