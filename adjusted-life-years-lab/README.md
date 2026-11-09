# QALY, DALY, HALY and PALY Interactive Lab

**Live site:** https://kareemelfass.github.io/HEOR-Interactive-Labs/adjusted-life-years-lab/

A standalone interactive learning site revised 9 November 2026. The site is hosted with the parent repository's GitHub Pages workflow and does not require a build step or back-end. The Markdown companion has been removed at the user's request.

## Teaching approach

The introductory fundamentals chapter explains what each metric means before calculations. Every QALY, DALY, HALY and PALY section begins with definitions and a worked example, then provides an interactive calculator or explorer, a cited published HEOR application and a specific caveats/pitfalls panel. The published examples are separate from the hypothetical cohort used in the interactive tools.

## What the learner can do

1. Review basics, definitions and the four interpretations of time, health loss and productivity.
2. Change duration, health utility and discounting, and see the explicit QALY calculation.
3. Calculate years of life lost (YLL), years lived with disability (YLD) and DALY burden, with separate incidence-duration and prevalence-year YLD conventions.
4. Explore Moreno-Ternero et al.'s HALY evaluation function and its reference-lifetime weight alpha.
5. Build an illustrative PALY productivity index using attendance, presenteeism, participation and productive years.
6. Recalculate the same five-year illustrative 100-person cohort across outcomes, reconstructing each annual calculation and export the inputs and results as CSV.
7. Complete a self-check quiz with explanations.

## Confirmed tutorial baseline

For 100 people over five years, before discounting:

| Outcome | Standard care | Treatment | Difference |
| --- | ---: | ---: | ---: |
| Life-years | 440.000 | 470.000 | +30.000 |
| QALYs | 300.300 | 357.750 | +57.450 |
| PALYs | 277.750 | 343.375 | +65.625 |
| Illustrative within-window morbidity shortfall | 139.700 | 112.250 | 27.450 averted |
| Finite-window total shortfall | 199.700 | 142.250 | 57.450 averted |
| Reference-based YLL from deaths in five years | 998.000 | 499.000 | 499.000 averted |
| Illustrative reference-based DALY burden | 1137.700 | 611.250 | 526.450 averted |

**Crucial:** Averted finite-window shortfall and reference-based DALYs measure different things. The latter uses assumed age-at-death remaining reference years beyond five years and cannot be directly compared with the five-year QALY total.

The values above are invented educational examples, not primary clinical or GBD estimates. Health utility and disability weight are set to complements only in the special mathematical exercise, not asserted as the general GBD method.

## Expanded concept-first chapters (9 November 2026 revision)

The lab now teaches the meaning of the four measures **before** offering a calculator:

- **Foundations:** One six-year patient history, a ten-year illustrative reference, utility 0.75 and productivity index 0.60. The worked example reconciles 4.5 QALYs attained, 1.5 matched-weight morbidity shortfall and 4 years of reference lifetime gap into 5.5 illustrative shortfall years. This is not a claim that actual GBD disability weights equal one minus utility.
- **QALYs:** Time in different utility states, area-under-the-utility-curve logic and a treatment-versus-comparator example separating quality and survival gains.
- **DALYs:** Distinction between health loss while alive and premature-mortality loss, a complete worked example, and why YLD can increase when an effective intervention extends survival.
- **HALYs:** Detailed derivation from attained health \(Q\) and missing health \(B=R-Q\) to \(P_\alpha=(1-\alpha)Q-\alpha B=Q-\alpha R\). Includes an adjustable patient-level health-budget diagram, a same-reference treatment comparison (\(\Delta P_\alpha\) invariant), and an explicitly distinct different-population comparison (ranking reverses when references differ).
- **PALYs:** Difference between time alive, health utility and productivity; constructive absenteeism/presenteeism arithmetic, the role of workforce participation and avoidance of double counting.

Every metric chapter also retains a cited published HEOR application and a substantive caveats/pitfalls section.

### Additional HALY acceptance tests

1. Open the individual HALY widget at defaults: 6 years, quality weight 0.75, reference 10 years and \(\alpha=0.5\).
2. Check 4.50 attained, 1.50 morbidity shortfall, 4.00 mortality gap, 5.50 total health shortfall and −0.50 evaluation score. The coloured bar should be 45%, 15% and 40%.
3. Change only \(\alpha\) to 1.00. The evaluation score must become −5.50 without changing the health history.
4. In the separate population comparison, equal references imply a +57.45 increment for every \(\alpha\).
5. Change Profile B's reference from 500 to 600, keeping A's reference 500: at \(\alpha=0.50\) the increment must be +7.45; at \(\alpha=1.00\), it must be −42.55. That is a comparison of different reference profiles, not evidence of a treatment effect.

## Published HEOR applications

- Sevilla JP et al. (2022): QALY-based Egyptian PCV programmes, [DOI](https://doi.org/10.1080/21645515.2022.2114252).
- Sibak M et al. (2015): DALYs averted by PCV13 vaccination in Egypt, [DOI](https://doi.org/10.1016/j.vaccine.2014.12.044).
- Marklund M et al. (2024): HALYs gained through Australian sodium benchmarks, [DOI](https://doi.org/10.1016/S2468-2667(24)00219-6). This is not a fitted application of the 2023 alpha family.
- Hird TR et al. (2019): PALY productivity burden of hypertension, [DOI](https://doi.org/10.1161/HYPERTENSIONAHA.118.12606).

## Primary sources

- Turner HC et al. (2026). *Quality-Adjusted and Disability-Adjusted Life Years: An Overview and Guide to Calculations.* https://doi.org/10.1007/s41669-026-00678-3
- Moreno-Ternero JD, Platz TT, Østerdal LP. (2023). *QALYs, DALYs, and HALYs: A unifying framework for the evaluation of population health.* https://doi.org/10.1016/j.jhealeco.2022.102714
- Ademi Z et al. (2025). *Scoping Review of Productivity-Adjusted Life Years: Methods, Applications and Policy Implications.* https://doi.org/10.1007/s40273-025-01544-6
- Ademi Z et al. (2021). *Productivity-Adjusted Life-Years: A New Metric for Quantifying Disease Burden.* https://doi.org/10.1007/s40273-020-00999-z

## Technical notes

- Open `index.html` directly, or use the live Pages URL.
- No external application services, analytics or login.
- MathJax is loaded from CDN. Core calculators and charts have no library dependencies.
- SVG charts and HTML tables update with the input sliders.
- Print-friendly styles and keyboard-accessible form controls are included.
- For a quick check, restore the integrated cohort's defaults and compare results to the table above.

## Suggested acceptance tests

- Set survival improvement scale to zero, treatment utility gain to zero and productivity gain to zero: all incremental cohort outcomes should equal zero.
- Restore defaults: incremental QALYs 57.45, PALYs 65.625 and reference-based DALYs averted 526.45.
- Change alpha in the integrated cohort: incremental HALY score remains equal to QALY gain when reference life is the same.
- In the HALY lesson, change the treatment reference total but keep the comparator fixed: incremental score should vary with alpha.
- In the DALY calculator, set deaths to zero: YLL should equal zero, while YLD may remain positive.
- In the QALY lesson, set utility to zero: QALYs should equal zero regardless of survival duration.
- Set discounting to 0% and then 3%: positive future QALYs and PALYs should decrease.
