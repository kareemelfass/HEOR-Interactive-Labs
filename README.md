# HEOR Interactive Labs

A growing collection of interactive, browser-based learning tools for **health economics and outcomes research (HEOR)** and **health technology assessment (HTA)**.

The focus is **learning by seeing and doing**: change model assumptions, follow calculations, inspect fitted and extrapolated curves, and see how methodological choices affect health economic models.

## Interactive labs

### 1. Mixture Cure Model Lab

Learn how mixture cure models represent cured and uncured latent populations, how cure probability can be modelled, and how expected mortality contributes to long-term survival extrapolation.

**[Open the Mixture Cure Model Lab repository](https://github.com/kareemelfass/mixture-cure-model-lab)**

Topics covered:
- Theoretical basis of mixture cure modelling
- Differences from other survival extrapolation approaches
- NICE DSU terminology and concepts
- When cure modelling may be appropriate
- Published HEOR and HTA examples
- Logistic modelling of cure probability
- Weibull survival for the uncured population
- Expected mortality for the cured population
- Interactive construction of the mixture survival curve
- HTA guidance and methodological references

---

### 2. Markov Model Basics Lab

Learn the mechanics of a simple three-state cohort Markov model by changing transition probabilities and watching the cohort move through Stable disease, Progressed disease, and Death cycle by cycle.

**[Open the Markov Model Basics Lab](https://kareemelfass.github.io/HEOR-Interactive-Labs/markov-model-basics/)**

Topics covered:
- Health states and absorbing states
- Transition probabilities
- Transition matrices and row-sum checks
- Cycle-by-cycle cohort movement
- Markov traces
- State occupancy over time
- State costs and utility weights
- QALY accumulation
- Worked first-cycle calculations

This introductory lab deliberately excludes discounting, half-cycle correction, tunnel states, time-varying transition probabilities, calibration, probabilistic sensitivity analysis, treatment comparisons, and microsimulation.

---

### 3. Semi-Markov Models in HEOR Lab

Build a semi-Markov cohort model from first principles and see exactly how time since state entry changes transition risks and cohort calculations.

**[Open the Semi-Markov Models in HEOR Lab](https://kareemelfass.github.io/HEOR-Interactive-Labs/semi-markov-model/)**

Topics covered:
- Why memory can matter in state-transition models
- Clock-forward versus clock-reset time
- Weibull sojourn survival and hazards
- Converting survival functions to cycle-specific transition probabilities
- Why aggregate state occupancy can be insufficient
- Tunnel states and state-duration tracking
- Costs, QALYs and treatment comparisons
- Competing transitions and cause-specific hazards
- Evidence sources for transition models
- Treatment effects, hazard ratios and extrapolation
- End-to-end four-cycle semi-Markov calculation

---

More HEOR labs will be added here as they are developed.
