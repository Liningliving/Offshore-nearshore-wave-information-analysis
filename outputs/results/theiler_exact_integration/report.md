# Exact elapsed-hour JIDT integration: accepted

The unmodified official source at commit `1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456` compiled locally using javac 21 with `--release 8`. The build file still labels itself 1.6.1; the exact commit and jar SHA-256 in `lib/jidt-official/build_manifest.json` distinguish this snapshot from the original released jar. All 250 Java source files compiled; estimator algorithms were not edited. The original jar remains available at `/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar`.

Official source: https://github.com/jlizier/jidt/commit/1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456

## Application changes

`ElapsedHourLoader.java` splits each series into consecutive hourly segments, passes the original elapsed-hour start index to `addObservationsTrackObservationIDs`, and uses observation-set ID 0 for every segment of that series. Each site uses independent calculator instances. The loader checks the actual Java time arrays, set arrays, observation counts and settings after finalization. It uses CPU execution and MI TIME_DIFF=0 for already aligned tuples. Both CMI variants use the same time-loading logic; direction is one two-dimensional predictor conditioned on Ho.

`WaveInformationExact.java` is a separate adapter for the compiled official jar. It preserves the original timing map for every observed and surrogate calculation. It reloads shuffled predictors into fresh calculators using the shared loader because base surrogate routines can rebuild observations with compressed time indices. This changes application loading only, not JIDT's estimator algorithms or the proposed null-model limitations.

## Actual Java tests

A 241-observation synthetic record contains hourly segments 0–79, 90–169, 240–319 and a singleton at hour 400. Tests confirm:

- k=4 and DYN_CORR_EXCL=45 are active inside MI, period CMI and direction CMI.
- Every stored observationTimePoints value equals its expected elapsed-hour index; every stored observationSetIndices value is 0.
- All 241 observations, including the singleton segment, are retained.
- Actual joint-tree candidate masks match the elapsed-hour rule for all 28,920 unordered pairs per calculator, with zero mismatches.
- The same exclusion holds in marginal searches and actual four-nearest-neighbour searches.
- Separations 44 and 45 hours are excluded; 46 hours remains eligible, within continuous segments and across gaps. A 71-hour separation across the long gap remains eligible.
- A negative control with different set IDs makes the 11-hour cross-segment pair eligible in both MI and CMI. This verifies why a shared series ID is essential.
- MI and both CMIs return finite synthetic estimates; jointly encoded direction uses dimensions (2,1,1).
- Synthetic shuffled-predictor reloads preserve all time metadata. End-to-end adapter smoke tests run all three measures with three synthetic surrogate draws each.

See `java_results.json`, `observation_indices.csv`, `pair_eligibility.csv`, smoke-test timing sidecars and `acceptance.json` for evidence.

## Real-site loading checks, without main analysis

| Site | Observations retained in all three calculators | Segments |
|---|---:|---:|
| Figure Eight Pools | 6,867 | 378 |
| Stockton | 10,522 | 265 |

Both cleaned files were loaded separately through the same Java helper. All actual Java time/set arrays match their timestamps. No main-data MI/CMI estimates were computed by this check. Hashes in `acceptance.json` confirm that cleaned datasets, autocorrelation outputs, selected 45-hour configuration, previous main results and the original fallback jar were unchanged.

## Status and reproduction

The exact Java adapter is verified. The earlier Python `information_analysis.py` still stops by default and has not yet been switched to the exact adapter. Previous main results are still the explicitly approximate row-window results; they are not superseded by these integration tests. No main analysis was rerun.

The compiled new jar, build provenance, license, application sources and test evidence are included in the project. The regenerable upstream checkout and Java class directories are ignored by git. To reproduce the build from official source:

```sh
git clone https://github.com/jlizier/jidt.git vendor/jidt-official
git -C vendor/jidt-official checkout 1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456
python3 src/build_jidt_official.py
python3 src/check_exact_theiler.py
```

The integration command requires Python with NumPy and a local JDK. It exits successfully only when the actual compiled implementation passes all checks. No interpolation, data trimming, autocorrelation rerun or change to the two-site research design was introduced.
