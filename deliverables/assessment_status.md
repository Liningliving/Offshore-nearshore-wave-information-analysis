# Assessment requirements and final scope

The final deliverable is a descriptive two-deployment scientific report. The professor permits deviations from the proposal; the user has explicitly chosen not to pursue another large calibration study or further inference-method development. That decision is reflected in the report, rather than silently treating a pilot as validation.

| Requirement or stated intention | Status in the final report | Remaining qualification |
|---|---|---|
| Physical motivation and Kinsela et al. framing | Addressed | Qualitative comparison; time-domain WHTH/Hsig differs from the paper's spectral Hm0 comparison. |
| Sampling interval for each buoy | Addressed | Offshore parameter records hourly, nearshore half-hourly; bulk-record interval is distinguished from raw motion sampling. |
| Usable samples and coverage | Addressed | N=6,867 /10,522, effectively hourly with gaps, separate dates and missing-hour counts. |
| Three continuous MI/CMI estimates per site | Completed previously; consolidated unchanged | Java integration is validated; that does not establish unbiased estimation or inferential calibration. |
| Direction treated as circular, joint predictor | Addressed | Two-component direction CMI conditions on offshore height; not separately summed cosine/sine contributions. |
| Direct comparison of sites | Addressed numerically | All three signed contrasts and hypothesis-consistency statements are explicit. **Numerical comparisons are not formal statistical tests.** |
| A way to investigate between-site significance | Investigated and documented | Whole-record subsampling failed pilot calibration. No adequately validated wave-data test was established. |
| Statistically confirmed differences / calibrated intervals or p-values | **Not achieved** | Remains unmet if the assessment requires successful formal inference. No significance claim, error bar or confidence interval is invented to fill the gap. |
| Surrogate significance analysis planned in the original proposal | **No validated wave significance result** | Step 8 stopped for unresolved null-model validity. Synthetic diagnostics are not substituted for real-data significance. |
| Autocorrelation and temporal exclusion | Completed previously; accurately described | Exact 45-hour exclusion across gaps is retained; residual dependence and nonstationarity remain. |
| Limited lag and exclusion sensitivity | Addressed using existing results | Both sample definitions and counts are explicit. Stable ordering is distinguished from changes in magnitude; ranges are not CIs or an optimized lag. |
| Remove unnecessary k sensitivity from main materials | Addressed | k=4 fixed in the report and selected figures; historical sensitivity files remain archived. |
| General causal effect of geomorphic setting | Not claimed | One site per setting and different years/depths prevent attribution solely to geomorphology. |
| Full submission/rubric compliance | Cannot certify from available material | The local `information theory hw-2.pdf` is the seven-page original project proposal, including hypotheses and planned methods, not a full marking rubric. No separate rubric, final video or submission package was supplied for this consolidation. |

## Suggested statement if asked about testing

> I directly compared the estimated information measures between the two deployment records. I also investigated statistical inference, but did not establish a sufficiently validated test for the between-site population differences. I therefore report the contrasts as descriptive findings, without p-values or confidence intervals. The height and direction predictions agree with the numerical orderings; the period prediction does not. None is formally accepted or rejected.

## Author review before submission

Verify institution-specific format, length, citation and AI-disclosure requirements against the actual rubric. The editable Word report is provided for this purpose. The earlier proposal's statement that AI only assisted brainstorming/wording would not describe all subsequent assistance: AI also assisted implementation, methodological evaluation and report drafting. Update the disclosure to reflect actual use; do not claim independent author verification that has not occurred. No signed author declaration has been fabricated in the report.
