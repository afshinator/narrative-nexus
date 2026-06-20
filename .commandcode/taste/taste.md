# ui-design
- Ensure text meets WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text). Muted/subtitle text must clear the threshold, not just be \"readable.\" Confidence: 0.85
- Include light/dark mode toggle in the UI. Confidence: 0.75
- Landing/home page should include contextual introduction explaining what the app is and what it currently tracks. Confidence: 0.75
- For dismissable intro/onboarding content, use an accordion-style expandable panel under the header (not a modal). Include a toggle button to roll/unroll it. Confidence: 0.85
- Accordion panels should be dismissable purely via the roll/unroll toggle — no "don't show again" checkbox or localStorage persistence. Confidence: 0.70

# ui-design
See [ui-design/taste.md](ui-design/taste.md)
# navigation
- Drill-down/detail pages should not be top-level navigation items; only accessible via click-through from parent views (e.g., source profile → cluster, timeline → article). Confidence: 0.70
