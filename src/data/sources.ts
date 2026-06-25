// Single source of truth for the default source panel.
// Per REQ-048–053: 20 sources across 5 tiers.
// Modify this array to change the default panel.

export interface Source {
	id: string;
	name: string;
	domain: string;
	tier: 1 | 2 | 3 | 4 | 5;
}

export const DEFAULT_SOURCES: Source[] = [
	// Tier 1 — Wire / Consensus Anchor (consensus pool)
	{ id: "reuters", name: "Reuters", domain: "reuters.com", tier: 1 },
	{ id: "ap", name: "AP", domain: "apnews.com", tier: 1 },
	{ id: "bbc", name: "BBC", domain: "bbc.com", tier: 1 },
	{ id: "npr", name: "NPR", domain: "npr.org", tier: 1 },
	{
		id: "the-guardian",
		name: "The Guardian",
		domain: "theguardian.com",
		tier: 1,
	},

	// Tier 2 — Mainstream Editorial (consensus pool + tracked)
	{ id: "fox-news", name: "Fox News", domain: "foxnews.com", tier: 2 },
	{ id: "politico", name: "Politico", domain: "politico.com", tier: 2 },
	{
		id: "the-economist",
		name: "The Economist",
		domain: "economist.com",
		tier: 2,
	},
	{ id: "nyt", name: "NYT", domain: "nytimes.com", tier: 2 },
	{
		id: "washington-post",
		name: "Washington Post",
		domain: "washingtonpost.com",
		tier: 2,
	},

	// Tier 3 — International (tracked only)
	{ id: "al-jazeera", name: "Al Jazeera", domain: "aljazeera.com", tier: 3 },
	{ id: "deutsche-welle", name: "Deutsche Welle", domain: "dw.com", tier: 3 },
	{ id: "nhk-world", name: "NHK World", domain: "www3.nhk.or.jp", tier: 3 },
	{
		id: "global-times",
		name: "Global Times",
		domain: "globaltimes.cn",
		tier: 3,
	},
	{ id: "france24", name: "France24", domain: "france24.com", tier: 3 },

	// Tier 4 — Independent / Investigative (tracked only)
	{
		id: "the-intercept",
		name: "The Intercept",
		domain: "theintercept.com",
		tier: 4,
	},
	{ id: "propublica", name: "ProPublica", domain: "propublica.org", tier: 4 },
	{ id: "bellingcat", name: "Bellingcat", domain: "bellingcat.com", tier: 4 },

	// Tier 5 — Contrarian (tracked only)
	{ id: "zerohedge", name: "ZeroHedge", domain: "zerohedge.com", tier: 5 },
	{
		id: "the-gray-zone",
		name: "The Gray Zone",
		domain: "thegrayzone.com",
		tier: 5,
	},
];

/** Pure function: group sources into a Record keyed by tier string. */
export function getSourcesByTier(): Record<string, Source[]> {
	const groups: Record<string, Source[]> = {};
	for (const source of DEFAULT_SOURCES) {
		const key = String(source.tier);
		if (!groups[key]) groups[key] = [];
		groups[key].push(source);
	}
	return groups;
}
