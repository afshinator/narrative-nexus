Fair. Let me actually walk you through it as if you'd never seen it — judge landing cold, me driving. No jargon, no internal round numbers. Here's the app.

---

**The problem I'm solving for you (10 seconds).** Everyone can tell you *what* the news said today. Nobody can tell you *which outlets to trust to be early and right* — which ones break real stories before everyone else, which ones just make noise, which quietly rewrite their articles after the fact. That's a blind spot for anyone whose money or decisions ride on news: hedge funds, PR firms, risk analysts. I built an instrument that measures it.

**How it works — the machine (45 seconds).** I open the **Pipeline** page. Four AI agents run in sequence: one reads articles from 37 news outlets across six continents and groups them by story; one strips the spin and pulls out the individual factual claims; one does pure math to find where independent outlets *converge* on the same claim — that convergence is what I call "consensus reality"; and one re-reads old articles to catch silent edits. I point at the provider dropdowns: every AI stage is running on **AMD Instinct hardware via Fireworks**, and it's swappable — the architecture isn't locked to one vendor. This is the "there's a real engine here, not a slideshow" moment.

**The payoff — the scatter (30 seconds).** Now I go to the **Sources** page. Every dot is an outlet, placed by two things: how often it breaks claims early (left-right) and how often those early claims actually survive into consensus (up-down). That splits the world into four corners — Early Breakers (early *and* right), Unmatched Breakers (early and wrong), the Reliable-but-late, and the Followers. In two seconds you can see how 37 outlets *behave*, not what they say. I click a dot — say NYT, up in the Early Breaker corner.

**The proof it's real (45 seconds).** That opens NYT's **profile** — its scorecard across six behavioral dimensions. Then I drill into an actual story to show the scores aren't magic. I open the **Venezuela earthquake** cluster: one event, 20 outlets, 138 extracted claims. At the top, three facts every major outlet agreed on — that's consensus forming. Below, the interesting part: NYT alone reporting Maduro was taken into custody, India's field hospital covered *only* by The Hindu, China's aid *only* by Global Times. You're watching the system separate what's corroborated from what's a single outlet's outlier. Then the **US-Iran War** cluster and its **timeline** — 48 days of a claim moving from one outlet's scoop to full consensus, animated.

**The close (10 seconds).** What you just saw is one verified run over a real 90-day news corpus. The product isn't the run — it's the instrument. Point it at the live feed and it accumulates behavioral history no competitor has, because nobody else is measuring this. The moat is time.

---

Now the honest part, since you asked me to sell it but you also pay me to not bullshit you: the sale above is real, but it leans on the *idea* landing fast, because the underlying corpus is small — 378 claims, 10 fully absorbed, two deeply-traced stories. The scatter is legitimately impressive at a glance; the scores underneath are demonstrative, not statistically weighty. That's fine for a hackathon judged on creativity, originality, and product potential — which is your track — as long as we lead with the concept and the machine, and let the data corpus be "one verified run," not "a mountain of evidence." Your instinct to freeze nothing is right until *you* believe that story.

So before I touch a README or a script: does that pitch match what you think you built — and where does it feel thin to you when you hear it out loud?


--- ---
