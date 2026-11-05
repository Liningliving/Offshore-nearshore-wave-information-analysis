# Primary information estimates: zero-lag MI and CMI

The exact elapsed-hour integration passed before final calculations. Only the six primary zero-lag estimates were calculated. No surrogate significance tests, propagation-lag calculations or sensitivity analyses were performed.

## Results

| Site | Measure | N | Nats | Bits |
|---|---|---:|---:|---:|
| figure_eight_pools | I(Ho;Hn) | 6867 | 1.072950521 | 1.547940396 |
| figure_eight_pools | I(Tp_o;Hn|Ho) | 6867 | 0.021167053 | 0.030537603 |
| figure_eight_pools | I((Dx,Dy);Hn|Ho) | 6867 | 0.067237007 | 0.097002497 |
| stockton | I(Ho;Hn) | 10522 | 0.471282925 | 0.679917538 |
| stockton | I(Tp_o;Hn|Ho) | 10522 | -0.006919212 | -0.009982313 |
| stockton | I((Dx,Dy);Hn|Ho) | 10522 | 0.160538110 | 0.231607535 |

All six use the original concurrent quality-filtered cleaned datasets. Dimensions (predictor, response, condition) are (1,1,0) for height MI, (1,1,1) for period CMI, and (2,1,1) for direction CMI. Dx and Dy are columns of one predictor array, not separately estimated or added. The heights remain the documented matching time-domain WHTH/Hsig definition, not spectral Hm0.

Height MI is descriptively larger at Figure Eight Pools. Direction provides a larger estimated conditional contribution at Stockton. Period CMI is small for Figure Eight Pools and near zero for Stockton. The negative Stockton estimate is retained: population CMI cannot be negative, but the finite-sample estimator can be. It should not be interpreted as negative information. These are point estimates without significance or uncertainty claims, and cannot establish a causal geomorphic explanation. Period and direction contributions can overlap and should not be added.

## Estimator settings and tie handling

Both sites use the CPU `MutualInfoCalculatorMultiVariateKraskov1` and `ConditionalMutualInfoCalculatorMultiVariateKraskov1` calculators with k=4, NORMALISE=true, NORM_TYPE=MAX_NORM, DYN_CORR_EXCL=45 exact elapsed hours, USE_GPU=false. One Java worker thread is used consistently. MI TIME_DIFF=0 because the supplied tuples are concurrent; the physical exclusion window is separate from propagation lag.

The stored measurements contain substantial ties, consistent with measurement rounding and discretized spectral parameters. Figure Eight Pools has 51 distinct Tp_o values and 190 distinct direction pairs among 6,867 observations; Stockton has 52 and 178 among 10,522. There are also 272 and 358 duplicate height-pair rows beyond their first occurrences. No complete five-variable tuples are duplicated. `ties_audit.csv` reports distinct counts, all rows in repeated groups, and duplicate rows beyond the first for each variable/tuple. These are exact-value tie counts on the existing stored data, not re-rounded values.

Use JIDT's KSG default Gaussian tie-breaking noise with NOISE_LEVEL_TO_ADD=1e-8 and NOISE_SEED=20261031, explicitly applied to every calculator at both sites. Official code adds this noise AFTER its own per-component normalization. The noise is in normalized units; no external jitter or normalization was added and no cleaned values were changed. A single seed makes each calculation reproducible, but different calculator dimensions consume the random sequence differently; this is not a claim that all measures receive identical per-variable perturbations. The level is negligible relative to the measurement resolution; these remain continuous-estimator approximations for quantized measurements.

Raw units returned by JIDT are nats. Bits are nats / ln(2). Both values and all requested metadata are saved in `primary_information_summary.csv`, including site, measure, sample size, dimensions, settings, Java/JIDT versions, commit/jar hash, noise settings, source CSV hash, timestamp hash and first/last retained timestamps.

## Official build and integration

Official repository: https://github.com/jlizier/jidt

Pinned current master commit: `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456` (3 August 2026).

The build file still labels the source version 1.6.1; this is a source snapshot with newer time-tracking support, distinguished from the old release jar by its commit and SHA-256. All 250 source files compiled with local javac 21.0.12.1 and `--release 8`. Estimator algorithms and official sources were not modified. Java runtime is OpenJDK 21.0.12.1. Build command/log/provenance are in `tools/jidt/build/build_manifest.json` and `build.log`. The original external 1.6.1 setup remains unchanged.

The Python runner reuses `hourly_indices` and `timed_blocks` from the existing autocorrelation/timestamp-aware helpers to validate timestamps and export the original hourly segments. Because JPype is not installed, Python invokes the compiled Java application adapter through subprocess. `ElapsedHourLoader.java` uses the same segment-loading contract: each contiguous hourly segment is added using `addObservationsTrackObservationIDs` with its ORIGINAL elapsed-hour start and the SAME observation-set ID 0. Sites run in separate Java processes with separate calculators. No padded observations enter JIDT.

After finalization the adapter checks the actual Java `observationTimePoints`, `observationSetIndices` and counts. Saved Java arrays are checked in Python against every original timestamp-derived index for all three calculators. Site segment counts are 378 and 265. Raw-data and cleaned files, preprocessing/autocorrelation code and outputs, selected 45-hour baseline and the fallback jar are SHA-256 protected; `preservation_checks.json` records that they are unchanged.

### Passed runtime checks

- All requested properties are read back from Java; synthetic subclasses additionally inspect the active protected k, window, normalization, norm, noise and seed fields.
- 241 synthetic observations span multiple hourly segments with missing intervals and a singleton segment. All are retained with correct actual time indices and set IDs.
- Across all 28,920 unordered pairs per calculator, the actual joint-tree eligibility masks exactly match |elapsed hours| > 45, with zero mismatches.
- Both joint and marginal searches and actual k=4 nearest-neighbour searches obey the exclusion.
- At 44 and 45 hours neighbours are excluded; at 46 hours they remain eligible, within segments AND across gaps. A 71-hour pair across a long gap remains eligible.
- A negative control deliberately using different set IDs permits an 11-hour pair across a gap in MI and CMI. This confirms why each site's segments must share an ID.
- MI and both CMI calculators run successfully; direction is jointly two-dimensional conditioned on Ho.
- Independent repeats produce exactly identical normalized/noised predictor arrays for all three calculators, and repeated synthetic outputs match with the fixed seed.
- Python validates the actual time/set arrays for every real-data observation in all six estimates, preserving original ordering and zero lag.
- All five automated tests pass, including the Java integration test. Existing Python helper tests alone are not used as proof of Java behaviour.

Evidence is in `integration/acceptance.json`, `java_results.json`, `observation_indices.csv`, `pair_eligibility.csv`, and the two sites' `*_java_indices.csv`, `*_segments.csv` and `*_retained_timestamps.csv` files.

## Reproduction

The upstream checkout and generated class files are ignored by git. With Python requirements installed and a local JDK:

```sh
git clone https://github.com/jlizier/jidt.git vendor/jidt-official
git -C vendor/jidt-official checkout 1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456
python3 src/build_jidt_official.py
python3 src/primary_information.py
python3 -m unittest discover -s tests
```

If the checkout already exists, reuse it at the pinned commit. `python3 src/primary_information.py --integration-only` runs only the integration gate. Any build/provenance or Java integration failure stops the script before final estimates. The main calculations always use the requested settings with the verified official build; there is no fallback to row-index exclusion.
