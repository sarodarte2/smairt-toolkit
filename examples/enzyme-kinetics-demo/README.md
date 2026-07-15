# Verified local enzyme-kinetics demo

This example starts with a clean virtual environment, installs SMAIRT, creates and configures a
project, validates a schema-8 scientific protocol, runs a local analysis, verifies immutable
provenance, records a human evidence decision, and prints final status. It does not use HPC.

Run from the repository root:

```bash
./examples/enzyme-kinetics-demo/run-demo.sh /tmp/smairt-enzyme-demo
```

For an offline source-checkout smoke test using an already installed development build, set
`SMAIRT_BIN=/path/to/smairt`. The normal path deliberately creates a fresh virtual environment and
installs the repository so installation failures are visible.

The fixed triplicate dataset was generated from `Vmax = 120.0 µmol/min` and `Km = 2.5 mM` with
zero-mean replicate perturbations. The analysis performs a nonlinear least-squares grid search and
must independently recover `Vmax` in `[119.9, 120.1]`, `Km` in `[2.49, 2.51]`, and a blank no larger
than `0.1 µmol/min`. Any mismatch exits nonzero. The final safety probe supplies a synthetic `.env`
request to SMAIRT's hook policy and confirms denial without opening a real protected file.

Semantic Scholar discovery is intentionally not required for correctness or repeatability. After
the demo, it can be tried separately with `smairt literature search "Michaelis Menten kinetics"
--provider semantic-scholar` when network access is appropriate.
