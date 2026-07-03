#!/usr/bin/env python3
"""D2a: Audit pairwise overlap between 15 labeled groups."""
GROUPS = {
    "US-Iran peace deal": {451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842, 2199, 169, 189, 153, 2198},
    "Venezuela earthquakes": {1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678, 772, 692, 567, 249, 1688},
    "World Cup 2026": {1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276, 1230, 1340, 1723, 1719, 1708},
    "Japan M7.2 earthquake": {1498, 134, 1525, 1863},
    "Messi at World Cup": {1752, 1746, 1737, 1732, 1727, 1726, 1723, 1719, 1703, 1698},
    "Trump birthright citizenship": {711, 2729, 2707, 2725, 3152, 2837, 2834, 453, 312, 118},
    "SNAP benefits cuts": {2078, 145, 2473},
    "Western Europe heat wave": {186, 244, 174, 1564, 135, 1483, 187, 193, 180, 175},
    "Israel-Gaza-Hezbollah": {168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910},
    "China-EU trade dispute": {1630, 1562, 1555, 1608, 1598, 1556, 1551, 1548, 764, 540},
    "Anthropic AI export ban": {157, 175, 486, 1493, 830},
    "Strait of Hormuz closure": {1518, 147, 131, 307, 306},
    "North Korea missile/navy": {336, 155, 1430, 2559, 3485},
    "Ukraine drone attack": {164, 277, 327, 1838},
    "Lebanon Hezbollah deal": {453, 2148, 2123, 1885, 2910},
}

names = list(GROUPS.keys())
print("Pairwise overlap matrix (shared article IDs):")
print(f"{'':25s}", end="")
for n in names:
    print(f"{n[:8]:>9s}", end="")
print()

for n1 in names:
    print(f"{n1:25s}", end="")
    for n2 in names:
        if n1 == n2:
            print(f"{'--':>9s}", end="")
        else:
            overlap = GROUPS[n1] & GROUPS[n2]
            if overlap:
                print(f"{len(overlap):>8d} ", end="")
            else:
                print(f"{'0':>9s}", end="")
    print()

# Detailed overlaps
print("\n\nDetailed overlaps (>=1 shared article):")
for i, n1 in enumerate(names):
    for j, n2 in enumerate(names):
        if i < j:
            overlap = GROUPS[n1] & GROUPS[n2]
            if overlap:
                print(f"\n  {n1}  ∩  {n2}")
                print(f"  Shared IDs ({len(overlap)}): {sorted(overlap)}")
