// Single source of truth for the default source panel.
// Per REQ-048–053: curated source panel across 5 tiers.
// Modify this array to change the default panel.

export type SourceRegion =
	| "na" // North America
	| "eu" // Europe
	| "me" // Middle East & North Africa
	| "asia" // Asia & Pacific
	| "africa" // Sub-Saharan Africa
	| "latam" // Latin America
	| "sa"; // South Asia

export interface Source {
	id: string;
	name: string;
	domain: string;
	tier: 1 | 2 | 3 | 4 | 5;
	region: SourceRegion;
}

export const DEFAULT_SOURCES: Source[] = [
	// Tier 1 — Wire / Consensus Anchor (consensus pool)
	{
		id: "reuters",
		name: "Reuters",
		domain: "reuters.com",
		tier: 1,
		region: "eu",
	},
	{ id: "ap", name: "AP", domain: "apnews.com", tier: 1, region: "na" },
	{ id: "bbc", name: "BBC", domain: "bbc.com", tier: 1, region: "eu" },
	{ id: "npr", name: "NPR", domain: "npr.org", tier: 1, region: "na" },
	{
		id: "the-guardian",
		name: "The Guardian",
		domain: "theguardian.com",
		tier: 1,
		region: "eu",
	},

	// Tier 2 — Mainstream Editorial (consensus pool + tracked)
	{
		id: "fox-news",
		name: "Fox News",
		domain: "foxnews.com",
		tier: 2,
		region: "na",
	},
	{
		id: "cnn",
		name: "CNN",
		domain: "cnn.com",
		tier: 2,
		region: "na",
	},
	{
		id: "cbs-news",
		name: "CBS News",
		domain: "cbsnews.com",
		tier: 2,
		region: "na",
	},
	{
		id: "abc-news",
		name: "ABC News",
		domain: "abcnews.go.com",
		tier: 2,
		region: "na",
	},
	{
		id: "politico",
		name: "Politico",
		domain: "politico.com",
		tier: 2,
		region: "na",
	},
	{
		id: "the-economist",
		name: "The Economist",
		domain: "economist.com",
		tier: 2,
		region: "eu",
	},
	{ id: "nyt", name: "NYT", domain: "nytimes.com", tier: 2, region: "na" },
	{
		id: "washington-post",
		name: "Washington Post",
		domain: "washingtonpost.com",
		tier: 2,
		region: "na",
	},

	// Tier 3 — International (tracked only)
	{
		id: "al-jazeera",
		name: "Al Jazeera",
		domain: "aljazeera.com",
		tier: 3,
		region: "me",
	},
	{
		id: "deutsche-welle",
		name: "Deutsche Welle",
		domain: "dw.com",
		tier: 3,
		region: "eu",
	},
	{
		id: "nhk-world",
		name: "NHK World",
		domain: "www3.nhk.or.jp",
		tier: 3,
		region: "asia",
	},
	{
		id: "global-times",
		name: "Global Times",
		domain: "globaltimes.cn",
		tier: 3,
		region: "asia",
	},
	{
		id: "france24",
		name: "France24",
		domain: "france24.com",
		tier: 3,
		region: "eu",
	},
	{
		id: "buenos-aires-times",
		name: "Buenos Aires Times",
		domain: "batimes.com.ar",
		tier: 3,
		region: "latam",
	},
	{
		id: "straits-times",
		name: "Straits Times",
		domain: "straitstimes.com",
		tier: 3,
		region: "asia",
	},
	{
		id: "the-hindu",
		name: "The Hindu",
		domain: "thehindu.com",
		tier: 3,
		region: "sa",
	},
	{
		id: "premium-times-ng",
		name: "Premium Times",
		domain: "premiumtimesng.com",
		tier: 3,
		region: "africa",
	},
	{
		id: "times-of-israel",
		name: "Times of Israel",
		domain: "timesofisrael.com",
		tier: 3,
		region: "me",
	},
	{
		id: "vanguard-ng",
		name: "Vanguard",
		domain: "vanguardngr.com",
		tier: 3,
		region: "africa",
	},
	{
		id: "the-reporter-et",
		name: "The Reporter",
		domain: "thereporterethiopia.com",
		tier: 3,
		region: "africa",
	},
	{
		id: "namibian",
		name: "Namibian",
		domain: "namibian.com.na",
		tier: 3,
		region: "africa",
	},
	{
		id: "punch-ng",
		name: "Punch",
		domain: "punchng.com",
		tier: 3,
		region: "africa",
	},
	{
		id: "jamaica-observer",
		name: "Jamaica Observer",
		domain: "jamaicaobserver.com",
		tier: 3,
		region: "latam",
	},
	{
		id: "mercopress",
		name: "MercoPress",
		domain: "en.mercopress.com",
		tier: 3,
		region: "latam",
	},
	{
		id: "tehran-times",
		name: "Tehran Times",
		domain: "tehrantimes.com",
		tier: 3,
		region: "me",
	},

	// Tier 4 — Independent / Investigative (tracked only)
	{
		id: "the-intercept",
		name: "The Intercept",
		domain: "theintercept.com",
		tier: 4,
		region: "na",
	},
	{
		id: "propublica",
		name: "ProPublica",
		domain: "propublica.org",
		tier: 4,
		region: "na",
	},
	{
		id: "bellingcat",
		name: "Bellingcat",
		domain: "bellingcat.com",
		tier: 4,
		region: "eu",
	},
	{
		id: "african-arguments",
		name: "African Arguments",
		domain: "africanarguments.org",
		tier: 4,
		region: "africa",
	},

	// Tier 5 — Contrarian (tracked only)
	{
		id: "zerohedge",
		name: "ZeroHedge",
		domain: "zerohedge.com",
		tier: 5,
		region: "na",
	},
	{
		id: "the-gray-zone",
		name: "The Gray Zone",
		domain: "thegrayzone.com",
		tier: 5,
		region: "na",
	},
	{
		id: "sputnik",
		name: "Sputnik",
		domain: "sputnikglobe.com",
		tier: 5,
		region: "eu",
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

/** Pure function: group active sources by region. */
export function getSourcesByRegion(
	sources: Source[],
	activeIds: string[],
): Record<string, Source[]> {
	const groups: Record<string, Source[]> = {};
	for (const source of sources) {
		if (!activeIds.includes(source.id)) continue;
		const key = source.region;
		if (!groups[key]) groups[key] = [];
		groups[key].push(source);
	}
	return groups;
}

export const REGION_LABELS: Record<string, string> = {
	na: "North America",
	eu: "Europe",
	me: "Middle East",
	asia: "Asia",
	africa: "Africa",
	latam: "Latin America",
	sa: "South Asia",
};

export const REGION_ORDER: SourceRegion[] = [
	"na",
	"eu",
	"me",
	"asia",
	"africa",
	"latam",
	"sa",
];
