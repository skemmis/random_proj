# Shooter accuracy benchmarks (round 2)

Compiled 2026-10-12. These notes feed the decision to model Crooks's accuracy from benchmark data and to use his real shots only as a sanity check.

Labels: **[S]** = a source states it. **[I]** = our inference or conversion. All σ values are per-axis standard deviations in MOA.

## Conversions [I]

| Quantity | Value at 135 m |
|---|---|
| 1 MOA | 3.93 cm |
| 1 mrad | 13.5 cm (3.438 MOA) |

Circular normal formulas, with σ as the per-axis SD:
- Mean radius = 1.2533σ
- CEP = 1.1774σ
- Probability of landing inside radius R = 1 − exp(−R²/2σ²)

Expected extreme spread is about 2.26σ for 3 shots, 3.05σ for 5 shots, and 3.7σ for 10 shots.

## 1. Benchmark datasets, converted to σ

| Study | Shooters / conditions | σ (MOA) [I] | Relevance |
|---|---|---|---|
| [ARL-TR-8594](https://apps.dtic.mil/sti/pdfs/AD1064518.pdf), Burcham 2018 | 16 sharpshooter+ soldiers, M4, prone supported, 8 s pop-ups | M68 red dot at 200 m: hit rate 0.897 → **3.2**. Iron sights at 200 m: 0.716 → 4.3 | High |
| [DRDC TR 2006-258](https://apps.dtic.mil/sti/pdfs/ADA478986.pdf), Tikuisis 2007 | 12 Canadian soldiers, 3.4× scope, prone, **125 m** pop-ups | Random **3.1**, plus a systematic offset of about **5.5** | High |
| [ARL-TR-7135](https://apps.dtic.mil/sti/pdfs/ADA611755.pdf), Shorter 2014 | 26 soldiers, M68 red dot, 50/100/150 m, 3.5 s exposures | About 3–5 (units inferred as inches) | High |
| [Kjellgren 1970](https://KRTraining.com/KRTraining/Archive/PracticalRangeSmallArms.pdf) | "Fair rifleman", prone, moderate stress, 2.5 × bench | About 2.5 | Medium |
| [Norway SOF 2022](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.894169/full) | 30 expert operators, 100 m prone unsupported | 1.5 at rest, 1.9 after exertion | Medium (expert floor) |
| [ARI RR 1678](https://apps.dtic.mil/sti/pdfs/ADA297284.pdf), Dyer 1995 | Soldiers, 25 m zero groups, untimed | 1.5–2.1 | Medium (lower bound) |
| [SALVO II](https://apps.dtic.mil/sti/pdfs/AD0325385.pdf), 1961 | Basic-training graduates, M1 iron sights, combat pop-ups | About 9.6 (experts 8.6, marksmen 10.7) | Medium (upper bound) |
| [AMSAA TR-461](https://apps.dtic.mil/sti/pdfs/ADA228398.pdf) / ARL-TR-2065 | Scoped snipers / match shooters | 1.0–2.75 / 0.34–1.0 | Low (floor) |

## 2. Stress and time multipliers on σ [I from S]

| Contrast | Multiplier on σ |
|---|---|
| Physical exertion (Norway SOF) | ×1.39 |
| Shoot-back threat (police, [Force Science](https://www.forcescience.com/2014/01/new-study-mental-imagery-boosts-shooting-accuracy-under-threat/)) | ×1.2 |
| 8 s → 4 s exposure (Stern & Yudowitch, cited in ARL-TR-8594) | ×1.36 |
| 8 s → 2 s exposure (same source) | ×2.3 |
| Sleep loss, heat, cold, noise (Tikuisis) | About ×1.0–1.1 |

## 3. Rifle and ammunition dispersion

- **M16 with M193 or M855:** 0.25 mil σ ≈ **0.86 MOA** ([AMSAA TR-461](https://apps.dtic.mil/sti/pdfs/ADA228398.pdf)). The M855 spec is ≤1.8 in SD at 200 yd ([Marsh 2011](https://ndia.dtic.mil/wp-content/uploads/2011/smallarms/Thursday12901Marsh.pdf)).
- **AR-15 with 55 gr ammunition:** about 0.65–1.2 MOA σ ([Criterion test](https://criterionbarrels.com/accuracy-analysis-of-different-types-of-ammunition-with-criterion-ar15-barrel)).
- **Prior [I]:** 0.9 MOA, range 0.7–1.3.

## 4. Bias (shared across a volley) vs random error

- **Bias is as large as random error, or larger.**
  - In Tikuisis, the mean distance from the aim point was 25 cm, while the group's mean radius was only 14 cm [S].
  - The Army treats a constant error of up to about 2.7 MOA as a "functionally accurate" zero ([USARIEM TN-01/2](https://apps.dtic.mil/sti/pdfs/ADA387108.pdf)) [S].
- **Zero distance** is unknown. At 150 yd it shifts the vertical impact by about −0.5 to +1.3 MOA [I].
- **Red-dot parallax** adds about 0.1–0.5 MOA at 135 m ([rifleconfigurator](https://www.rifleconfigurator.com/tools/how-a-red-dot-works)) [I/S].
- **Cant** is negligible (≤0.3 MOA) [I].
- **Wind** of 5 mph moves the impact about 1 MOA [I].

## 5. Recommended prior for Crooks [I]

His benign σ is plausibly 2.3–3.0 MOA. He had about 43 range sessions and no formal training, fired self-supported prone, and used a 1×, 2 MOA dot.

| Term | Prior |
|---|---|
| Shot 1 random σ (stressed, deliberate) | LogNormal(ln 3.2, 0.35): median 3.2 MOA, 90% interval 1.8–5.7 MOA (12.6 cm at 135 m) |
| Vertical vs horizontal σ | Vertical ≈ 1.1–1.2 × horizontal |
| Shots 2–3 | Shot-1 σ × LogNormal(ln 1.5, 0.25) |
| Bias per volley, horizontal | N(0, 2 MOA) |
| Bias per volley, vertical | N(+0.5, 2.5 MOA) |
| Re-aim before shots 4–8 | Redraw the bias |

**Sanity check:** a head is about 15 × 23 cm, roughly equivalent to a circle of radius 2.7 MOA. With σ = 3.2 MOA and no bias, the chance of a hit is about 0.29. With 2 MOA of bias it drops to about 0.2.

## 6. House Task Force report: what we could read

- **What remains unread.** The final report's "Shots Fired" (p. 43) and Quantico trajectory pages (pp. 128–129) are still unread. Our fetch tool truncates the PDF at about p. 41, and the proxy blocks direct download. The PDF is at [taskforce.house.gov](https://taskforce.house.gov/sites/evo-subsites/july13taskforce.house.gov/files/evo-media-document/12-5-2024-Final-Report-Redacted.pdf).
- **From [Higgins's additional views](https://clayhiggins.house.gov/wp-content/uploads/2024/12/Higgins-additional-views-J13-TF-Report.pdf) [S]:**
  - Crooks fired from "a self-supported prone position at the ridge/peak," "150 yards from his target."
  - "shots 1, 2 and 3 were carefully fired in 1.55 seconds at a standing, clear line of sight target," then "adjusted his aim downwards" for shots 4–8.
  - "Crooks' firing position was also several feet back from the actual peak."
  - "one of Crooks' shots hit a pressurized hydraulic line on a staged piece of heavy equipment."
  - The FBI has given no analysis of where the casings were found.
