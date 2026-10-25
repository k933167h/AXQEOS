# Seeded-defect benchmark (synthetic harness check)

Two intentionally wrong examples in `lab/fixtures/seeded_defects.py`:
- D001: discount mistakenly added to amount, correctness failure
- D002: authorization inverted, security failure

Run `python -m pytest -q tests/test_seeded_benchmark.py`.

The seeded adapter is **deterministic** and knows exactly what patterns to look for. The trusted oracle checks whether the known defective code string exists and returns exit code zero when the seeded defect is present. The gate must return HOLD with two verified critical/high findings. The negative-control test ensures both oracle checks reject corrected code.

**Limitations:** This is a controlled integration/smoke benchmark. It does not measure AI model discovery accuracy, does not establish causal model benefit, and is not a general semantic correctness oracle. CI status must be checked before treating it as passing.

**Next real trial:** operator installs supported CLI versions, runs review over a permission-approved fixed Git SHA in an OS-isolated sandbox, assesses AI findings against independent defect IDs, manually adjudicates uncertain claims, and records paired baseline/pilot active-review minutes. Avoid exposing hidden ground truth to models in any real evaluation; keep these synthetic fixtures out of the held-out scoring set.

No Harness² or LLMWiki rollout before the human-signed evidence gate.
