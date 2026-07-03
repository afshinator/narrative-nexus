    S1. DONE. resolution.py:27-33 — insufficient corroboration falls through to day≥90
        → UNRESOLVED. agent3_consensus.py:70-73 passes reporting to determine_state.
        T1b tests (test_phase1.py): 10 passed.
          test_min_corroboration_constant PASSED
          test_single_source_rejected PASSED
          test_two_source_accepted PASSED
          test_same_source_dupes_merge PASSED
          test_cross_source_merges PASSED
          test_below_threshold_no_merge PASSED
          test_idempotent PASSED
          test_threshold_boundary PASSED
          test_excludes_claims_within_7_days PASSED
          test_no_as_of_returns_all PASSED
    
    S2. DONE. embedding_client.py:38-45 — MODEL_DIMS dict keys on model name.
        agent1_intake.py:67-94 — loads cached embeddings WHERE model=? AND
        article_id IN (...), then skips rows where dim != expected_dim with
        skipped_dim counter and log. Mismatch guard: line 93-94.
    
    S3. DONE. scripts/recluster_all.py exists (321 lines). RUN against live
        data/nn.db (default --db). Evidence: 1,179 clusters (was 4,499), max
        cluster 1,934 claims (cluster includes claims from 30 sources per S5 query).
        DB directly modified — clusters DELETEd and recreated, claims.cluster_id
        reassigned.
    
    S4. NOT DONE. scripts/tune_clustering.py has 15 story groups with article IDs
        (e.g. 1851-1853 for Iran-US strikes). scripts/eps_sweep.py targets
        /tmp/phase2.db which does not exist. No sweep results table found in any
        file or session. Real story groups may or may not resolve — never executed.
    
    S5. Live data/nn.db WAS modified:
          claims:          7,747 (was 8,567 per old vault)
          ABSORBED:           13
          PENDING:         6,224
          UNRESOLVED:      1,510
          claim_sources:   8,114
          claim_variants:    932
          clusters:        1,179
        Backup files: data/nn-pre-phase2-* → NOT FOUND.
        /tmp/dryrun.db exists (30MB, Jul 2) — dry-run copy, not a backup.
    
    S6. Pytest: 163 passed, 2 failed, 15 skipped
        Vitest: 147 passed, 11 failed, 4 skipped (1 file, router-shell.test.tsx)
    
    S7. git status: clean
        Commits:
          b031a4b revise plan a
          22c1e4c Further research for project pivot
          1ef0159 Task A refactor done
          8a258f5 pivot to fix big probs!
          a52ae2d Phase 2: T1-T7 complete — zombie fix, embedding hygiene, recluster,
                   claim matching, consensus fix, truth sync
    
    S8. Run the T4 eps sweep (tune_clustering.py) to find optimal DBSCAN epsilon,
        then validate with actual story-group article IDs in the live DB.