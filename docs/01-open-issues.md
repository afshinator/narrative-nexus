# Open Issues — Narrative Nexus

Items that need investigation or resolution but aren't blocking current work.

---

## Self-improvement notification spam

**Observed:** "Self-improvement review: Patched SKILL.md in skill 'ponytail' (1 replacement)" repeats every ~10 minutes during sessions using the ponytail skill.

**Investigation so far (2026-07-02):**
- Found and removed a duplicate "rtk vitest edge case" pitfall entry in ponytail/SKILL.md
- Found 184 escaped-quote sequences (`\"`) throughout the file — replaced with literal quotes (`"`) but this was likely a no-op (both render the same in Markdown)
- YAML frontmatter parses correctly, prose renders correctly after changes
- Web search / Hermes docs inaccessible during investigation (Firecrawl down)

**Unknown:**
- What triggers the self-improvement mechanism
- Whether it's project-specific (ponytail skill content), harness-specific (Hermes self-improvement feature), or independent (platform-level behavior)
- Whether the notifications have stopped after the fixes applied

**No action needed now** — the notifications are harmless noise. Investigate when Hermes docs are accessible or when the pattern recurs.
