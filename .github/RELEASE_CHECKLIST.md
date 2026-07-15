# Maintainer Release Checklist

This checklist does not authorize or announce a release. Follow
[the release process](../docs/development/release.md) and record the reviewer for every manual gate.

- [ ] CI, Security, dependency-range, documentation, and clean-wheel jobs pass.
- [ ] Dependency changes receive GitHub dependency review, or a documented manual dependency diff
      while this repository remains a fork.
- [ ] Functional scientific-invariant and failure-recovery tests pass.
- [ ] WSL and compact, normal, and wide terminal smoke tests pass.
- [ ] Experimental safety and controlled-data limitations are reviewed.
- [ ] Version, changelog, installation instructions, and proposed tag agree.
- [ ] The unchanged MIT license text and copyright line have been reviewed for the fork.
- [ ] Software authorship and citation guidance have been reviewed before restoring `CITATION.cff`.
- [ ] A genuine private conduct-reporting route exists before restoring a Code of Conduct.
- [ ] About text, topics, social preview, support routes, branch protection, and checks are reviewed.
- [ ] Wheel, source distribution, checksums, SBOM, and attestations are attached.
- [ ] PyPI publication remains disabled unless separately approved.
