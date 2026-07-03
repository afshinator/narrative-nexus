# F2 Autopsy — 3 CONSENSUS_ABSORBED Claims on Copy B


## Claim 2863: A grizzly bear in Canada threatened a woman and a dog.
  Source: abcnews (tier 2)
  Cluster: 6990, Absorbed: 2026-07-03T19:37:48.723847+00:00, Convergence: CROSS_SOURCE_CONVERGENT

### Variants merged (3):
```
  id=1676 [nytimes] first_seen=
  text: A woman in Alberta, Canada recorded a grizzly bear.
  id=1677 [nytimes] first_seen=
  text: A grizzly bear circled a woman and her dog near a campsite and lodge in Alberta, Canada.
  id=1678 [nytimes] first_seen=
  text: A grizzly bear galloped toward a woman in the Canadian Rockies.
```

### Cluster 6990 stats:
  Distinct sources: 3, Claims: 10

### Sample article titles (5):
```
  [foxnews] Woman stalked by charging bear on morning dog walk captures terrifying encounter on camera
  [abcnews] WATCH:  Grizzly bear in Canada threatens woman and dog, video shows
```

### Absorption math:
  Pool T1/T2 sources (3): ['abcnews', 'foxnews', 'nytimes']
  Reporting (claim_sources): 2
  Reporting (variants): 1
  Total T1/T2: 3
  pct = 3/3*100 = 100.0% (threshold=65)
  MIN_CORROBORATION=2: PASS

## Claim 4037: The woman was stalked by a large bear.
  Source: foxnews (tier 2)
  Cluster: 6990, Absorbed: 2026-07-03T19:37:48.728388+00:00, Convergence: CROSS_SOURCE_CONVERGENT

### Variants merged (2):
```
  id=1674 [foxnews] first_seen=
  text: The bear initially slowly moved toward the woman.
  id=1675 [abcnews] first_seen=
  text: The bear closed in on the woman and the dog.
```

### Cluster 6990 stats:
  Distinct sources: 3, Claims: 10

### Sample article titles (5):
```
  [foxnews] Woman stalked by charging bear on morning dog walk captures terrifying encounter on camera
  [abcnews] WATCH:  Grizzly bear in Canada threatens woman and dog, video shows
```

### Absorption math:
  Pool T1/T2 sources (3): ['abcnews', 'foxnews', 'nytimes']
  Reporting (claim_sources): 2
  Reporting (variants): 2
  Total T1/T2: 4
  pct = 4/3*100 = 133.3% (threshold=65)
  MIN_CORROBORATION=2: PASS

## Claim 4145: Thunderstorms caused severe delays to hundreds of flights at Heathrow Airport.
  Source: theguardian (tier 1)
  Cluster: 6994, Absorbed: 2026-07-03T19:37:48.734122+00:00, Convergence: CROSS_SOURCE_CONVERGENT

### Variants merged (1):
```
  id=1681 [bbc] first_seen=
  text: Many delays are due to thunderstorms.
```

### Cluster 6994 stats:
  Distinct sources: 2, Claims: 10

### Sample article titles (5):
```
  [bbc] Thunderstorms delay hundreds of Heathrow and Gatwick flights
  [theguardian] Thunderstorms disrupt Gatwick and Heathrow as hundreds of flights delayed or cancelled
```

### Absorption math:
  Pool T1/T2 sources (2): ['bbc', 'theguardian']
  Reporting (claim_sources): 2
  Reporting (variants): 1
  Total T1/T2: 3
  pct = 3/2*100 = 150.0% (threshold=65)
  MIN_CORROBORATION=2: PASS

## Raw merge log lines (deduplicated from 1,626 total)

```
merge: claim 1961 → canonical 4145 (sim=0.8018) [Many delays are due to thunderstorms.]
merge: claim 2864 → canonical 4037 (sim=0.8316) [The bear closed in on the woman and the dog.]
merge: claim 4043 → canonical 4037 (sim=0.8481) [The bear initially slowly moved toward the woman.]
merge: claim 5965 → canonical 2863 (sim=0.8048) [A woman in Alberta, Canada recorded a grizzly bear.]
merge: claim 5966 → canonical 2863 (sim=0.8201) [A grizzly bear circled a woman and her dog near a campsite and lodge in Alberta,]
merge: claim 5968 → canonical 2863 (sim=0.8004) [A grizzly bear galloped toward a woman in the Canadian Rockies.]
```


## Verdicts

Claim 2863 (bear + woman + dog): LEGITIMATE — same real-world bear encounter in Canada. ABC canonical, 3 NYT variants merged at sim 0.80-0.82. Cluster 6990: 3 distinct sources, all about the same bear incident.
Claim 4037 (woman stalked by bear): LEGITIMATE — sub-claim of same bear story. Fox canonical, Fox+ABC variants merged at sim 0.83-0.85. Same coherent cluster 6990.
Claim 4145 (Heathrow thunderstorms): LEGITIMATE — Guardian canonical, BBC variant merged at sim 0.80. Cluster 6994: 2 distinct T1 sources, same weather event.
