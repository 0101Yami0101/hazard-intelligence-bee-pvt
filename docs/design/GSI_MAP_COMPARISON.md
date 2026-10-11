# SlopeSense's susceptibility map against GSI's 50 m national map

The roadmap's last open exit check for the susceptibility model
(ROADMAP_LANDSLIDE.md, "comparison against GSI's 50 m benchmark map").

Code: `scripts/model/compare_gsi_susceptibility.py` →
`reports/gsi_susceptibility_comparison.json`. Nothing in the app changes.

## 1. Method, written before it was run (2026-10-10)

**The two maps**

| | SlopeSense | GSI |
|---|---|---|
| File | `data/processed/susceptibility_oof.parquet` (scores) | `data/raw/10_context/gsi_landslide-susceptibility_50m_arunachal.tif` |
| Grain | 100 m, a score from 0 to 1 | 50 m, three classes: Low, Moderate, High |
| How it is scored here | each cell by a model that **never saw that cell's region** (five spatial folds) | as published |

**The test set:** the 544,794 cells the SlopeSense model was built and
tested on — 90,799 landslide cells and 453,995 other cells (slopes over
10°, at least 500 m from any mapped landslide, five per landslide cell).
GSI's class is read at each cell's centre. Only cells where GSI has a
class are compared, and the share that have one is reported.

**What is measured, on the same cells for both maps**

1. **Ranking.** How often a landslide cell is ranked above a non-landslide
   cell (AUC). GSI has only three classes, so most pairs tie; a tie counts
   as half, the standard way. Reported for all cells and for each of the
   five regions.
2. **Like for like.** GSI's High class covers some share of the land. Take
   the same share of land from the top of SlopeSense's score. Which holds
   more of the landslides? The same for High + Moderate.
3. **Landslides GSI's map-makers did not have.** GSI built its map from
   its own landslide inventory, which is also most of this test set. So GSI
   is being marked on landslides it has seen and SlopeSense on ones it has
   not. The fairer cut is the landslides mapped only by NRSC Bhuvan /
   APSAC (2014, 2017, 2023 surveys) and not in GSI's inventory: measure 1
   and 2 again on those alone.
4. **An outside list.** NASA's landslide catalogue points inside the state
   (already used as the independent check in the roadmap): the share of
   them on GSI's High class against the share on SlopeSense's top land of
   the same size. These points are located to about a kilometre, so this is
   a coarse check. For this one SlopeSense's shipped map
   (`susceptibility.tif`) is used, since the catalogue was not training data.
5. **Where they disagree.** Cells GSI calls High and SlopeSense puts in its
   bottom half, and cells GSI calls Low and SlopeSense puts in its top
   tenth: how many are there, and what share of each are landslide cells?

**How it will be read**

- SlopeSense is "at least as good" if it is not behind on 1 and 2, on all
  cells and on the Bhuvan-only cut. It is "better" if it is ahead on both
  in the Bhuvan-only cut, the fair one.
- Whatever the result, three things are stated beside it: GSI's map is
  national and three-class by design; it has seen most of these
  landslides; and "landslide cells" are mapped landslides, which are
  easier to find near roads.
- A result where GSI is ahead is reported the same way.

## 2. Result (2026-10-10)

GSI has a class on 93% of the test cells (99% of the landslide cells); the
comparison is on those 508,138 cells.

| Measure | SlopeSense | GSI |
|---|---|---|
| **Ranking, all cells** (landslide above non-landslide, times in 100) | **85** | 60 |
| Ranking, by region (five) | 83 to 87 | 56 to 66 |
| **Ranking, landslides only Bhuvan mapped** (26,430 cells) | **86** | 58 |
| Ranking, landslides in GSI's own inventory (63,139 cells) | 85 | 60 |
| **GSI's High class is 13.8% of the land.** Share of landslides on it, against SlopeSense's top 13.8% | **67%** | 25% |
| The same, Bhuvan-only landslides | **69%** | 22% |
| **GSI's High + Moderate is 53% of the land.** Share of landslides on it, against SlopeSense's top 53% | **94%** | 68% |
| The same, Bhuvan-only landslides | **94%** | 67% |
| NASA catalogue points (55 where both maps have a value), on GSI's High against SlopeSense's same-size top | 38% | 16% |
| The same for High + Moderate | 80% | 51% |

**Where they disagree** (17.6% of all test cells are landslide cells):

| Cells | How many | Share that are landslides |
|---|---|---|
| GSI says High, SlopeSense puts them in its bottom half | 26,232 | 4% |
| GSI says Low, SlopeSense puts them in its top tenth | 30,152 | 48% |

**Read by the rule set in §1:** SlopeSense is ahead on ranking and on
like-for-like capture, on all cells and on the Bhuvan-only cut. By the rule
that is "better", not just "at least as good". It holds in every one of the
five regions.

**What GSI's map does do.** It is not noise: landslides are 12.5% of its Low
cells, 19% of its Moderate and 28% of its High, and over the whole state,
flat land included, it ranks a landslide above other land 59 times in 100.

**What must be said beside these numbers**

- GSI's map is a national map in three classes, made for the whole
  country by one method. SlopeSense is fitted to this one state at 100 m
  with a continuous score. A local model beating a national one on its home
  ground is the expected result, not a surprising one.
- GSI is marked here on landslides it had; SlopeSense on ones it had not.
  That only makes the gap conservative.
- "Landslide cells" are mapped landslides, which are easier to find near
  roads. Both maps are marked against the same list, so this does not
  favour either.
- The NASA check is 55 points located to about a kilometre: a coarse
  confirmation, not a measurement.
- Neither map is a probability. This compares how well each one ranks
  ground, nothing else.

## 3. The first copy of GSI's map was wrong — found by this test

The first run of this comparison gave GSI a ranking of **50 in 100 — pure
chance**, with the same mean slope in all three of its classes. That is not
a believable result for a published map, so the file was checked before
anything was concluded.

- A fresh, small export of the same area matched the stored file on **41%**
  of cells — about what chance gives for three classes.
- Moving the stored file about did not help: its (weak) best fit was not at
  zero offset.
- **Cause:** the July download asked the server for the whole state as one
  image in longitude/latitude and took its default resampling. What came
  back had the right outline and the right mix of classes, and the wrong
  class in most cells.
- **Fix** (`scripts/fetch/fetch_18_hazard_products.py`): the map is now
  fetched on GSI's own grid (EPSG:32644, 50 m, snapped to its origin) in 35
  tiles with nearest-neighbour. On that grid a 500, a 2,000 and a 4,000 px
  request agree cell for cell.
- **The new copy checks out:** its ranking peaks exactly at zero offset
  (0.595) and falls in every direction; landslide share rises with its
  class; its no-data edge follows the state (a class on 85% of cells inside
  the state, 2% outside).

Nothing else used the old file except a picture in `scripts/viz/extract.py`,
which now reads the new grid. GSI's map has never been a model input, so no
model is affected.

**The lesson kept:** a result that says an official map is worthless is
first a reason to check our own copy of it.

## 4. What this allows us to say

- "Against the same landslides, SlopeSense's top 14% of ground holds about
  two-thirds of them; the national map's High class, the same amount of
  ground, holds about a quarter."
- Not: "GSI's map is wrong." It is a national screening map and it does
  rank ground better than chance.
