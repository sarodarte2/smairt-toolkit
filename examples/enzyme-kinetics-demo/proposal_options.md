## Option A: Nonlinear Michaelis-Menten recovery

### Hypothesis
Nonlinear fitting will recover the independently declared Vmax and Km within their tolerances.

### Reasoning and Evidence
The fixed substrate series follows the Michaelis-Menten relationship; doi-a04d8aaf11d84cfac807 supplies
historical context, while correctness is tested against independent generating values.

### Falsifiable Prediction
Vmax will be 119.9 to 120.1 and Km will be 2.49 to 2.51, with blank velocity at most 0.1.

### Null or Competing Explanation
The implementation, aggregation, or model may be wrong and fail one or more declared checks.

### Required Data and Proposed Test
Use all fixed triplicates and blanks, fit the nonlinear model once, and compare with locked ranges.

### Feasibility, Confounders, and Risks
The run is local and deterministic; synthetic simplicity limits external scientific interpretation.

### Difference from Other Options
This tests the model in its native nonlinear form and directly estimates both parameters.

## Option B: Linearized reciprocal estimate

### Hypothesis
A Lineweaver-Burk transformation will recover compatible parameter estimates.

### Reasoning and Evidence
The reciprocal transformation is a scientifically distinct estimation route, though it changes
the error structure and can over-weight low substrate concentrations.

### Falsifiable Prediction
Transformed estimates will fall inside separately predeclared tolerances.

### Null or Competing Explanation
Transformation-induced weighting will cause biased estimates despite correct source data.

### Required Data and Proposed Test
Transform nonzero concentration means, fit a line, and convert slope and intercept to Vmax and Km.

### Feasibility, Confounders, and Risks
It is easy to run but statistically less appropriate for this fixture and sensitive near zero.

### Difference from Other Options
This tests a linearized estimator rather than the native nonlinear relationship.

## Option C: Constant-rate null model

### Hypothesis
A concentration-independent rate explains the observations as well as the saturating model.

### Reasoning and Evidence
This explicit null asks whether substrate concentration contributes useful structure at all.

### Falsifiable Prediction
The constant-rate residual error will be no worse than the nonlinear model error.

### Null or Competing Explanation
The saturating model will fit substantially better, rejecting the constant-rate explanation.

### Required Data and Proposed Test
Fit the grand mean to nonzero observations and compare prespecified residual errors.

### Feasibility, Confounders, and Risks
The comparison is deterministic but is not a general model-selection study.

### Difference from Other Options
This challenges the need for a kinetic curve instead of estimating Michaelis-Menten parameters.
