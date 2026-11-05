# Presentation speaker script

Target: approximately 10 minutes at a measured pace. Slides 1–12 are narrated; slide 13 is a reference slide. Adjust to the actual assessment time limit.

## Slide 1 — Offshore–nearshore wave dependence

How closely do offshore waves describe conditions near the coast, and does that relationship differ between coastal settings? This project compares Figure Eight Pools and Stockton using mutual information and conditional mutual information. The aim is to quantify dependence, including additional information associated with offshore period and direction. Throughout this presentation, the differences are descriptive findings from two deployment records. They are not statistically confirmed population differences or evidence that coastal geometry caused the patterns.

## Slide 2 — Why compare these settings?

The motivation comes from Kinsela and colleagues, who compared the same buoy pairings and reported greater offshore–nearshore height scatter at Stockton. An exposed coastline may retain a more consistent connection with the regional offshore wave field, while an embayment may respond differently to changing approach direction. This motivates three predictions: higher height MI at Figure Eight Pools, and higher period and direction CMI at Stockton. These are predictions about information relationships, not direct measurements of attenuation. My height variables are time-domain significant heights, whereas Kinsela used spectral significant height, so this is a related investigation rather than an exact replication.

## Slide 3 — Two buoy pairings, different deployments

Figure Eight Pools is paired with the Port Kembla, or Wollongong, offshore station. Stockton is paired with Sydney. The original offshore parameter records are hourly and the nearshore records half-hourly. Exact concurrent matching produces effectively hourly observations with gaps: 6,867 complete observations at Figure Eight Pools and 10,522 at Stockton. These counts refer to the joint complete dataset used for all three primary measures. The deployments occur in different years and cover different durations, so this is not a simultaneous comparison under identical weather or seasonal conditions.

## Slide 4 — From buoy records to aligned observations

Preprocessing checked the supplied metadata and selected matching time-domain significant wave heights: offshore WHTH and nearshore Hsig. Peak period comes from WPPE and peak wave direction from WPDI. Nearshore fixed-AEST timestamps were converted to UTC before exact matching with offshore records. Quality flags and complete required variables determine the retained observations. Heights can be nonnegative and periods must be positive. Valid large waves are retained, and gaps are not interpolated. Direction is represented by cosine and sine together, preserving the circular connection between directions near zero and 360 degrees.

## Slide 5 — What do MI and CMI measure?

Height MI measures dependence between offshore and nearshore height without restricting the relationship to a straight line. Period CMI asks how much additional dependence period has with nearshore height after conditioning on offshore height. Directional CMI asks the corresponding question for joint direction. Neither conditional measure controls for the other predictor, so their values cannot be added as separate, non-overlapping contributions. Values are in bits, converted from JIDT’s nats by dividing by the natural logarithm of two. They do not express a percentage of explained variance, wave energy loss, or a causal influence.

## Slide 6 — A consistent estimator across both sites

Both sites use the same continuous Kraskov algorithm one estimators with four nearest neighbours, normalization and the maximum norm. The existing autocorrelation analysis selected a common 45-hour Theiler window. This excludes temporally nearby observations as candidate neighbours. A key implementation check was to preserve actual elapsed-hour indices across missing observations, rather than counting retained rows. Java checks confirmed that observations 44 and 45 hours apart are excluded, while those 46 hours apart remain eligible across gaps. Small reproducible noise handles rounded measurement ties. These checks establish correct implementation; they do not prove unbiased estimation or independent observations.

## Slide 7 — Main results: direct site comparisons

The main comparison shows a height MI of about 1.548 bits at Figure Eight Pools and 0.680 bits at Stockton. The Figure-Eight-minus-Stockton difference is positive 0.868023 bits, consistent with the height prediction. Directional CMI is about 0.097 bits at Figure Eight Pools and 0.232 at Stockton, giving a Stockton-minus-Figure-Eight difference of positive 0.134605 bits. Period CMI is small: approximately 0.031 and negative 0.010 bits, giving a difference of negative 0.040520 bits. Its ordering is opposite the period prediction. Negative estimated CMI reflects finite-sample estimation, not negative physical information. No significance markers or uncertainty intervals are shown.

## Slide 8 — Height relationships in the observations

The scatterplots provide physical context for the information estimates. Offshore height is on the horizontal axis and nearshore height on the vertical axis, with matching scales for both sites. The dashed line marks equal wave height, rather than a fitted regression. The saved Pearson correlations are approximately 0.940 at Figure Eight Pools and 0.798 at Stockton. This descriptive pattern agrees with the height-MI ordering. However, MI is not attenuation: an invertible rescaling of wave height can change attenuation without changing population MI. Greater dependence should therefore not be interpreted directly as weaker energy loss.

## Slide 9 — Do the site orderings persist?

Temporal sensitivity changes one setting at a time. Positive lag compares offshore conditions at time t with nearshore height at t plus the lag. The main lag plots use common source timestamps within each site: 6,316 at Figure Eight Pools and 10,307 at Stockton. These differ from the primary samples. Across zero, half, one and two hours, the height contrast ranges from about 0.820 to 0.923 bits, while the directional contrast decreases from about 0.141 to 0.084 bits. Both site orderings persist. Theiler windows of 30, 45 and 60 hours also retain both orderings, with smaller magnitude changes. These are robustness checks, not confidence intervals or significance tests.

## Slide 10 — Physical interpretation: partial support

The findings partially support the original predictions at the descriptive level. More consistent offshore–nearshore height dependence at Figure Eight Pools is compatible with its exposure. Greater directional CMI at Stockton is compatible with direction-dependent sheltering or transformation. These are plausible physical interpretations alongside Kinsela’s findings, not mechanisms demonstrated by this analysis. Period CMI may be small because offshore height already carries related information, or because one peak period incompletely describes mixed sea and swell. Rounding and finite-sample effects may also matter. None of these possibilities was separately tested, and small CMI does not establish that period is physically unimportant.

## Slide 11 — What the comparison can—and cannot—show

A between-site statistical test was investigated because the central question compares two records. One time-block interval method was piloted on synthetic data but did not achieve adequate initial calibration. It was not used to report wave-data confidence intervals or p-values. That supplementary investigation does not mean all possible methods fail. The scientific conclusion remains descriptive. Different years, seasonal coverage, depths, local conditions and sample sizes complicate attribution, while one site per setting prevents generalising a geomorphic effect. The Theiler window does not remove every form of temporal dependence. A stable ordering across sensitivity settings is useful, but it cannot substitute for validated statistical inference.

## Slide 12 — Conclusion

The main contribution is a reproducible information-theoretic comparison of two coastal deployment records. Figure Eight Pools shows stronger offshore–nearshore height dependence. Stockton shows greater additional dependence associated with offshore peak direction after offshore height is known. Period contributes little estimated conditional information and does not follow the predicted ordering. The height and direction orderings persist under the tested temporal choices, although their magnitudes are not equally stable. Together, the results extend the physical comparison with information measures while keeping the conclusions within the evidence: descriptive deployment differences, without established population significance or geomorphic causation.

## Slide 13 — References and reproducibility

Use this slide for reference or questions. The repository contains the original data, preprocessing audits, Java integration evidence, saved estimates and sensitivity results. The final scientific report provides full references and methodological limitations.
