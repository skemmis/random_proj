# ANSUR II (2012) male head and neck measurements: summary

**Source:** ANSUR II public data, male file `ANSUR_II_MALE_Public.csv`, from Penn State OpenLab
(https://www.openlab.psu.edu/ansur2/, direct file http://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv).
The data come from the 2012 Anthropometric Survey of US Army Personnel (Gordon et al., 2014, NATICK/TR-15/007) and were released publicly in 2017.
**Licence:** The OpenLab page does not state a licence. The survey is a US Government (US Army Natick) work, so it is
presumed public domain under 17 U.S.C. 105. Please cite Gordon CC et al. (2014), *2012 Anthropometric Survey of U.S. Army
Personnel: Methods and Summary Statistics*, NATICK/TR-15/007.

**Units:** all lengths are in mm. `weightkg` is in kg here; the source column is in hectograms and was divided by 10. `interpupillarybreadth` is recorded in 0.1 mm in the source and was divided by 10 to give mm. `age` is in years.
**Note:** this is a military sample (age 17-58), not the US civilian population.

Extracted columns: `ansur2_male_head.csv` (4082 men, 22 columns).

## All men (n = 4082)

| measure | mean | SD | P5 | P50 | P95 |
|---|---:|---:|---:|---:|---:|
| stature | 1756.2 | 68.6 | 1648.0 | 1755.0 | 1870.0 |
| weightkg | 85.5 | 14.2 | 64.4 | 84.6 | 110.7 |
| earlength | 64.2 | 4.5 | 57.0 | 64.0 | 72.0 |
| earbreadth | 36.1 | 3.0 | 31.0 | 36.0 | 41.0 |
| earprotrusion | 23.2 | 3.0 | 19.0 | 23.0 | 28.0 |
| headbreadth | 154.3 | 5.5 | 146.0 | 154.0 | 163.0 |
| headlength | 199.5 | 7.0 | 188.0 | 200.0 | 211.0 |
| headcircumference | 574.4 | 16.0 | 548.0 | 574.0 | 601.0 |
| tragiontopofhead | 131.1 | 6.2 | 121.0 | 131.0 | 141.0 |
| neckcircumference | 397.6 | 25.8 | 360.0 | 395.0 | 443.0 |
| neckcircumferencebase | 434.6 | 25.7 | 395.0 | 433.0 | 479.0 |
| bitragionchinarc | 331.7 | 14.0 | 309.0 | 332.0 | 355.0 |
| bitragionsubmandibulararc | 315.7 | 16.6 | 289.0 | 315.0 | 345.0 |
| bizygomaticbreadth | 142.6 | 6.2 | 133.0 | 143.0 | 153.0 |
| mentonsellionlength | 122.6 | 6.7 | 112.0 | 123.0 | 134.0 |
| interpupillarybreadth | 64.0 | 3.4 | 58.5 | 64.0 | 70.0 |
| eyeheightsitting | 804.5 | 33.2 | 750.0 | 804.0 | 860.0 |
| sittingheight | 918.3 | 35.7 | 860.0 | 918.0 | 977.0 |
| cervicaleheight | 1517.3 | 63.3 | 1416.0 | 1517.0 | 1622.9 |
| suprasternaleheight | 1438.6 | 61.2 | 1341.0 | 1437.0 | 1540.0 |

## Men aged 50+ with stature >= 185 cm (n = 10)

| measure | mean | SD | P5 | P50 | P95 |
|---|---:|---:|---:|---:|---:|
| stature | 1875.9 | 25.8 | 1852.3 | 1864.5 | 1914.8 |
| weightkg | 97.5 | 19.4 | 73.2 | 98.2 | 122.2 |
| earlength | 68.4 | 5.5 | 63.5 | 65.5 | 77.1 |
| earbreadth | 38.8 | 3.0 | 34.8 | 38.5 | 42.6 |
| earprotrusion | 22.3 | 3.8 | 16.9 | 23.0 | 26.0 |
| headbreadth | 154.6 | 5.5 | 147.4 | 155.5 | 161.8 |
| headlength | 204.4 | 3.6 | 199.3 | 204.5 | 209.2 |
| headcircumference | 579.7 | 12.4 | 565.3 | 578.5 | 599.0 |
| tragiontopofhead | 132.8 | 7.0 | 123.3 | 134.0 | 141.6 |
| neckcircumference | 403.8 | 35.3 | 358.3 | 412.0 | 453.6 |
| neckcircumferencebase | 441.2 | 28.9 | 401.1 | 450.0 | 475.6 |
| bitragionchinarc | 338.7 | 19.3 | 312.6 | 342.5 | 362.2 |
| bitragionsubmandibulararc | 321.6 | 21.2 | 294.4 | 321.0 | 354.7 |
| bizygomaticbreadth | 140.0 | 7.9 | 132.9 | 136.5 | 153.5 |
| mentonsellionlength | 129.9 | 7.6 | 119.2 | 131.0 | 140.0 |
| interpupillarybreadth | 66.7 | 4.5 | 60.5 | 67.8 | 72.0 |
| eyeheightsitting | 834.1 | 24.9 | 804.4 | 831.0 | 871.0 |
| sittingheight | 949.6 | 28.2 | 917.8 | 949.5 | 990.4 |
| cervicaleheight | 1634.7 | 22.2 | 1610.7 | 1628.5 | 1669.9 |
| suprasternaleheight | 1550.9 | 30.6 | 1516.3 | 1543.5 | 1587.7 |

Percentiles are empirical (pandas linear interpolation). The second subgroup is very small, so treat its P5 and P95 values as rough.
Also for reference: men aged 50+ of any stature, n = 119, and men with stature >= 185 cm of any age, n = 359.

## Larger subgroups (means +/- SD, mm)

| measure | age >= 50 (n=119) | stature >= 185 cm (n=359) |
|---|---:|---:|
| stature | 1753.1 +/- 66.8 | 1884.1 +/- 31.0 |
| weightkg | 90.0 +/- 12.9 | 97.9 +/- 15.6 |
| earlength | 67.8 +/- 4.7 | 66.0 +/- 4.5 |
| earbreadth | 38.2 +/- 3.1 | 36.9 +/- 3.1 |
| earprotrusion | 23.4 +/- 3.3 | 23.5 +/- 3.0 |
| headbreadth | 155.5 +/- 5.9 | 155.0 +/- 5.5 |
| headlength | 199.5 +/- 6.8 | 203.3 +/- 6.5 |
| headcircumference | 574.4 +/- 15.7 | 582.5 +/- 14.9 |
| tragiontopofhead | 130.2 +/- 7.2 | 133.2 +/- 5.8 |
| neckcircumference | 410.7 +/- 29.0 | 405.1 +/- 27.1 |
| neckcircumferencebase | 442.8 +/- 27.8 | 446.1 +/- 26.1 |
| bitragionchinarc | 337.2 +/- 13.9 | 338.4 +/- 13.5 |
| bitragionsubmandibulararc | 323.1 +/- 15.4 | 322.8 +/- 16.6 |
| bizygomaticbreadth | 144.0 +/- 6.9 | 143.9 +/- 6.4 |
| mentonsellionlength | 123.5 +/- 7.2 | 126.4 +/- 6.8 |
| interpupillarybreadth | 65.4 +/- 3.5 | 65.0 +/- 3.4 |
| eyeheightsitting | 798.2 +/- 31.5 | 851.6 +/- 24.1 |
| sittingheight | 909.2 +/- 34.7 | 970.4 +/- 25.2 |
| cervicaleheight | 1520.8 +/- 64.1 | 1632.9 +/- 30.7 |
| suprasternaleheight | 1441.0 +/- 60.1 | 1551.3 +/- 29.9 |
