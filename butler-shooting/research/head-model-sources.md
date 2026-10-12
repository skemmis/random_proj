# 3D head model: sources and licensing (round 2)

Compiled on 2026-10-12. The decision is a recognizable Trump likeness at maximum detail, plus an internal anatomy layer used to classify hits as vital or non-vital.

## Key facts

- **No real 3D scan of Trump is publicly available.** Every "Trump model" online is a hand sculpt or AI output, so geometric accuracy is limited by the photo references whichever route we take.
- **No ear model can be trusted.** Neither existing models nor open photo-to-3D tools recover a person-specific ear accurately. The right ear has to be modeled by hand against calibrated photos.
- **Trump's head and ear have never been measured publicly.** We estimate them instead:
  - Ear length ≈ 55.9 + 0.22 × age mm, so about 73 mm at 78 ([Heathcote 1995](https://www.bmj.com/content/311/7021/1668)).
  - Priors and plausibility bounds come from the ANSUR II columns `earlength`, `earbreadth`, `earprotrusion`, `headbreadth` and `tragiontopofhead` ([ANSUR II](https://www.openlab.psu.edu/ansur2/)).
  - Scale is calibrated from his height (191 cm) and known objects in the photos.

## Candidate likeness meshes

| Model | License | Faces | Notes |
|---|---|---|---|
| [shortlan "Donald bust no shape keys"](https://sketchfab.com/3d-models/donald-bust-no-shape-keys-26f94485f4e244bbaa9c98fa492d06bd) | CC-BY | 656k | Hand-modeled in Blender. Best free candidate. |
| [jasonli0415 "Donald Trump"](https://sketchfab.com/3d-models/donald-trump-70962bdc07894b9db10d36818d0c0761) | CC-BY 4.0 | 1.44M | Unknown how it was made; check for AI artifacts. |
| [entropy9ine](https://sketchfab.com/3d-models/donald-trump-2da060b16a7a4995913c78b059bfc341) | CC-BY | 28k | Rigged, with blendshapes. |
| [RenderHub imlegal bust](https://www.renderhub.com/imlegal/donald-trump-realistic-bust) | Editorial only, $39 | 12.2M | Sculpt. |
| [TurboSquid Emotion #2](https://www.turbosquid.com/3d-models/donald-trump-emotion-2-1139360) | Editorial only, $199 | 663k | Sculpt. |

Avoid: [MyMiniFactory](https://www.myminifactory.com/object/3d-print-donald-trump-high-quality-stl-file-for-3d-printing-personal-use-348100) (CC-BY-NC-ND, no derivatives allowed) and the scan of a rubber Halloween mask.

## Base meshes (CC0)

- MPFB2 / MakeHuman: output is CC0.
- [Blender Studio Human Base Meshes](https://www.blender.org/download/demo-files/#assets).
- FLAME 2023 Open: CC-BY 4.0, but its license bans "misleading" content.

## Photo-to-3D tools

- **Commercial use OK:** 3DDFA_V2 (MIT) does face only with no ears, but it is good for measuring head pose from video frames.
- **Research only (non-commercial):** DECA, EMOCA, MICA, NextFace, and the Universal Head Model, which has the best statistical ear model.
- **Image-to-3D generators** (TRELLIS, MIT) invent the ear, so they are useful only for a quick blockout.

## Internal anatomy

| Source | License | Contents |
|---|---|---|
| [BodyParts3D](https://dbarchive.biosciencedbc.jp/data/bodyparts3d/20110915/README_e.html) | CC-BY-SA 2.1 JP | Skull, brain, carotid and vertebral arteries, jugular veins, cervical spine, spinal cord. Units must be verified. |
| [Z-Anatomy](https://github.com/Z-Anatomy/The-blend) | CC-BY-SA 4.0 | Blender files. Strip the NC sub-models (inner ear, kidney) before commercial use. |
| [SPL Head and Neck Atlas](https://openanatomy.org/atlas-pages/atlas-spl-head-and-neck.html) | Slicer license (permissive) | Skull, spine and vessels; no brain. |

Keep the anatomy as a separate layer so the share-alike license doesn't extend to the likeness mesh.

## Reference photos

- **Public domain:** US-government photos (White House, DVIDS). On Wikimedia Commons, filter by `PD-USGov-POTUS`.
- **CC-BY-SA, credit required:** Gage Skidmore and Michael Vadon photos.
- **Copyrighted:** July 13 photos (AP, NYT, Getty). Use them for private reference only unless licensed.

## Recommended path

- **Commercial article:** CC0 base plus our own sculpt, using the CC-BY Sketchfab meshes as reference, then a hand-modeled right ear and a BodyParts3D anatomy layer.
- **Non-commercial article:** the research tools above are also available.
