# D2b: Revised label set — 13 groups (down from 15)
# Merges: World Cup+Messi (2), Israel+Hezbollah+Lebanon (3-way merge)
# Article 175 removed from heat wave (was Anthropic, not climate)

LABELED_GROUPS_V2 = [
    # 1. Unchanged
    ("US-Iran peace deal", [
        451, 1745, 1522, 1492, 345, 133, 2175, 789, 1255, 1842,
        2199, 169, 189, 153, 2198,
    ]),
    # 2. Unchanged
    ("Venezuela earthquakes", [
        1491, 1695, 106, 332, 2216, 2048, 2201, 1687, 2200, 1678,
        772, 692, 567, 249, 1688,
    ]),
    # 3+5 MERGED: World Cup 2026 + Messi at World Cup (share 1719,1723; same event)
    ("World Cup 2026 (+Messi)", [
        1748, 1720, 1933, 1650, 1641, 838, 1263, 1328, 1275, 1276,
        1230, 1340, 1723, 1719, 1708, 1752, 1746, 1737, 1732, 1727,
        1726, 1703, 1698,
    ]),
    # 4. Unchanged
    ("Japan M7.2 earthquake", [
        1498, 134, 1525, 1863,
    ]),
    # 6. Unchanged (article 453 removed — it's Lebanon/Israel, not birthright)
    ("Trump birthright citizenship", [
        711, 2729, 2707, 2725, 3152, 2837, 2834, 312, 118,
    ]),
    # 7. Unchanged
    ("SNAP benefits cuts", [
        2078, 145, 2473,
    ]),
    # 8. FIXED: article 175 removed (it's Anthropic AI, mislabeled)
    ("Western Europe heat wave", [
        186, 244, 174, 1564, 135, 1483, 187, 193, 180,
    ]),
    # 9+15 MERGED: Israel-Gaza-Hezbollah + Lebanon Hezbollah deal (5 shared; same war)
    ("Israel-Hezbollah conflict", [
        168, 2184, 2173, 453, 1861, 1239, 2148, 2123, 1885, 2910,
    ]),
    # 10. Unchanged
    ("China-EU trade dispute", [
        1630, 1562, 1555, 1608, 1598, 1556, 1551, 1548, 764, 540,
    ]),
    # 11. Unchanged
    ("Anthropic AI export ban", [
        157, 175, 486, 1493, 830,
    ]),
    # 12. Unchanged
    ("Strait of Hormuz closure", [
        1518, 147, 131, 307, 306,
    ]),
    # 13. Unchanged
    ("North Korea missile/navy", [
        336, 155, 1430, 2559, 3485,
    ]),
    # 14. Unchanged
    ("Ukraine drone attack", [
        164, 277, 327, 1838,
    ]),
]
