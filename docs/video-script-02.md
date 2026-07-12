# Narrative Nexus — Video Script Revision (video-script-02)


## [Open]
*Start on the Sources page, don't click yet.*

> Everyone can tell you *what* the news said today. 
>
>But who can answer some questions you might want answered about who gives you the news: 

>How mainstream is any given source? 

>Which ones break real stories first — unique, and ahead of the pack? 

>And which just echo consensus after it's already been published elsewhere? 

>Narrative Nexus is an instrument that answers them. It doesn't score bias — it scores behavior, measured over time.

---

## [The machine]
*Navigate to Pipeline.*

Four AI agents run in sequence. 

One reads articles from 37 news outlets across six continents and groups them by story. 

One strips the spin and extracts individual factual claims. 

One does pure math to find where independent outlets *converge* on the same claim — that convergence is what we call consensus reality. 

And one re-reads old articles to catch silent edits. 
 

Every AI stage runs on Fireworks AI — that's inference on AMD Instinct hardware — and each stage's provider is configurable. 

And that configurability is tested, not decorative: we deployed Gemma 4 E4B on-demand through Fireworks and verified it running our claim-extraction prompt across the full sixty-one-article Venezuela cluster — 268 structured claims extracted, evidence in the repo.

The shipped database itself was built on the default Fireworks DeepSeek configuration. This is a real engine, not a slideshow.

---

## [The scatter]
*Navigate to Sources, gesture across the plot.*

> Every dot is an outlet, placed by two behaviors: how often it breaks claims early, and how often those claims survive into consensus. That splits the world into four corners — Early Breakers, early and validated; Unmatched Breakers, early but uncorroborated; Late but Reliable; and Consensus Echoes. In two seconds you can see how 37 outlets *behave*, not what they say. *(click a dot)* Clicking any dot opens that outlet's full profile — six behavioral dimensions, no single composite score.

---

## [The proof]
*Navigate to Stories.*

> Two real stories, processed end to end. *(open the Venezuela cluster report)* The Venezuela emergency — a five-day surge: 20 outlets, 138 claims, 5 silent edits detected. At the top, the facts independent outlets converged on. Below, the interesting part — single-outlet claims the system refuses to self-validate: one source alone reporting Maduro was taken into custody, India's field hospital covered only by The Hindu, China's aid only by Global Times. That refusal isn't cosmetic — it's the hardest lesson we learned. Our first engine reported 2,625 consensus claims; almost all of them were an artifact — a single source in a cluster of one, agreeing with itself at a hundred percent. We rebuilt it: consensus now requires at least two independent sources reporting the same claim, matched across outlets at cosine similarity of point-eight-five or higher. Twenty-six hundred claims collapsed to 10 real ones. *(back to Stories, open the US-Iran timeline)* And the US-Iran war — a 48-day arc, animated claim by claim, from one outlet's first report to cross-source consensus.

---

## [Close]
*Back on Sources.*

> What you've seen is one verified run over a real news corpus — nothing mocked; every number traces back to a query. This run was short by design, to prove the pipeline works end to end. The real product is the instrument itself — as far as we've found, nobody profiles how news sources behave over time the way this does. Run it continuously and that behavioral record only gets richer: the moat is time. Built to tell the clones from the outliers, Narrative Nexus tracks consensus reality — not truth.

