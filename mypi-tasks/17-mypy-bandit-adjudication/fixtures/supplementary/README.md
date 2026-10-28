# Supplementary mypy run

The collector's own mypy invocation produces **3 diagnostics and stops**, because the scanned
tree contains one file that is not valid Python:

```
scripts/v1_concurrency_test.py:6  ->  "{file}....[truncated]"   (literal, not Python)
```

mypy has no continue-past-syntax-error mode, so it exits 2 having checked almost nothing. That
result is kept in the sample as its own cohort (`mypy/syntax`, frame 3) rather than dropped.

`mypy-excluding-broken-file.jsonl` is the same tree measured with that one file excluded, so the
type signal on the other 118 files can be adjudicated:

```
mypy --output json --no-error-summary --explicit-package-bases \
     --ignore-missing-imports --exclude 'v1_concurrency_test\.py' --cache-dir /tmp/... .
```

Produced 2026-10-28 with the pinned `<prefix>/python/bin/mypy` 2.4.0 on commit `07d9f1b`,
`exit 1`, 28 diagnostics.

`--ignore-missing-imports` is also in the collector's manifest invocation. The audit prefix
installs no scanned repo's dependencies, so uninstalled third-party imports dominate: without the
flag the same run reports 139 diagnostics of which **111 are `import-not-found`**, and the 28
that remain are byte-identical with or without it. The flag silences the venv, not the type check.

**Declared exclusion:** the one file above is out of the *measurement*, not out of the repo. It
carries its own three `syntax` verdicts in the sample, and the report must say that excluding it
is what makes 28 rows exist.
