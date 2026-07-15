# Analysis: EXPERIMENT_001 / ITERATION_001

## Executive Summary

The deterministic local analysis recovered the known Michaelis-Menten parameters and passed the
blank-control check.

## Observed Results

The fitted values were Vmax = 120.0 micromoles per minute and Km = 2.50 millimolar. The maximum
absolute blank velocity was 0.1 micromoles per minute.

## Interpretation

The recovered values match the independently declared generating values. This supports the narrow
claim that the demo analysis and SMAIRT provenance path behave correctly for this fixture.

## Limitations and Confounders

The dataset is synthetic and deliberately well behaved. It demonstrates computational correctness,
not biological discovery or general model adequacy.

## Decision

Accept only after SMAIRT verifies the run bundle and result-summary checksums.

## Next Steps

Use a real dataset only after defining domain-appropriate controls and uncertainty analysis.
