# The home page: the idea, told on the page (2026-10-12)

**Why.** The home page was one compact screen: the platform's name and the
module tiles. The user asked for "a real landing page" that explains the
whole idea and project, and that matches the presenter's script closely
enough to be presented from directly.

**What it is now.** The first screen is unchanged in purpose (name, one
line, the module tiles, the Data Backbone strip), so a forecast is still
one click away. Below it the page tells the story in five numbered parts,
the same order as the script's slides
([PRESENTATION_SCRIPT.md](../PRESENTATION_SCRIPT.md)):

| Part | Headline (same as the deck) | What is on screen | Deck slides |
|---|---|---|---|
| 1 The problem | The facts already exist. They do not fit together. | Six source cards, each a different grid; the four walls as tiles | 2 |
| 2 The idea | Do the hard part once. Build everything on top. | Four steps as tiles, the football-field card, the stack of four layers | 3 |
| 3 How it works | One pipeline, and a way back | Five boxes, the dashed line that leaves under Serve and returns under Collect, three figures, six of the rules we keep in mind, **Open** for the Data Backbone | 4, 5 |
| 4 Running today | A product is a question asked of the backbone | Where × when, the two products with a picture and an **Open** button each, the reuse table and "2 files", then **More about SlideSense / FloodSense** | 6 to 10 |
| 5 What comes next | What else can stand on it | Three directions, the loop as a ring, the three steps as stairs, the closing line and "where you come in" | 11 to 13 |

A slim bar fixed to the top of the page jumps to any part; ◎ goes back to
the top. (The script had a matching section, "Presenting from the home
page", until the user had the script cut down to the words alone on
2026-10-12; the page still follows the slides part for part.)

## Second pass, the same day (the user's five points)

1. **A little of the company's look.** Taken from beesolutions.in (its code
   is on this PC at `D:\CODE\BeeDigital\SolutionsApp`): gold `#F5A623` /
   `#FFD85C` on near-black, the bee mark, small technical labels in Space
   Grotesk with numbered sections. Used lightly: a "by BEE Solutions" tag
   under the title (bee mark, links to the site), gold section numbers
   ("01 //"), the labels in Space Grotesk, a gold "BEE Solutions" line and a
   faint honeycomb corner on the closing block, "built by BEE Solutions" in
   the footer. The app's teal and blue stay the main colours; gold is kept
   away from anything that shows a hazard level (both are warm).
2. **"More about SlideSense" / "More about FloodSense"** at the end of part
   4: two rows that open in place (no page reload; opening one closes the
   other). Each says the questions it answers, what is on its screens, how
   to read it (the five levels or bands as a colour strip) and who it is
   made for, with one honest line on what it is not. **By the user's rule
   they say nothing about how a forecast is made, what was collected for
   it, or how well it scores**: no counts of landslides or gauges, no
   sources, no methods, no accuracy.
3. **"Glacial-lake floods" removed** from "More hazards"; "Drought and dry
   spells" added in its place, dashed (planned), not as a main one. The
   deck's slide 11 and the script's words were changed to match, so the
   three stay in step.
4. **More pictures, fewer words, nothing crooked.** The source cards are no
   longer tilted; the walls and the four steps are tiles with icons; the
   pipeline's "way back" is a drawn line; the six rules are one line each;
   the loop is a ring; the three steps are stairs. Text was cut throughout.
   Icons are CSS masks (`_ICONS` in `landing.py`), so they need no icon
   font and take the colour of the text.
5. **A background that says what the project is:** two faint mountain
   ridges along the bottom of the window, the nearer one filled with a
   square grid. Mountains cut into squares is the whole idea. It is on the
   home page only (`.stApp:has(.st-key-land_wrap)`).

## Where the code is

- `webapp/core/landing.py`: every block of the story as a function that
  returns one line of HTML, plus its CSS (`.lp-*`). Read its opening note
  before editing: it explains why each block must be a single line and why
  `p`, `h2`, `h3`, `ul`, `li` are swapped for plain `div`s on the way out
  (Streamlit styles those tags itself and outranks a single class).
- `webapp/app.py`: the first screen as before, then
  `st.container(key="land_story")` with the blocks in order. Real Streamlit
  buttons sit in containers keyed `tile_story_<module>`; the click-to-cover
  splash (`core/splash.py`) reads the module's name and colour from
  `.lp-prod` / `.lp-prod-name` there, as it does from the tiles.
- `webapp/assets/landing/bee.webp` (10 KB): the company's bee mark, cut
  down from the site's logo.
- `webapp/assets/landing/slidesense.webp`, `floodsense.webp` (85 KB
  together): the two module pictures. Retake with
  `python scripts/run/capture_landing_shots.py` whenever those screens
  change. A missing picture leaves an empty frame; the page still opens.
- The figure "29 sources" is read from the Data Backbone's own catalogue
  (`assets/backbone/catalogue.json`). "8.2 million squares" and "26 years"
  are fixed at the top of `landing.py`.

## Rules for the wording (it is a public page)

- No accuracy figures and no built/planned status board: the same rule the
  user set for the client deck on 2026-10-07. Each product is described by
  what it asks, what it gives and what it reads.
- Anything not live is drawn dashed and called planned (the open feed, the
  further hazards, other states, the paid step).
- Same phrases as the script, so the page and the talk reinforce each
  other: "do the hard part once", "a product is a question asked of the
  backbone", "2 files", "code can be copied", "an app is a vehicle, the
  backbone is the road".
- No state other than Arunachal is named (see "Known" below).
- The "More about" panels: what a module answers, shows and is for.
  Never how it works inside, what data was gathered, or how accurate it
  is (the user, 2026-10-12).
- No contact button: the user chose to end on the three "where you come
  in" chips only.

## Checked (2026-10-12)

| Check | Result |
|---|---|
| All screens open (`scripts/run/check_app_screens.py`, now 35 cases: the home page is the new one) | pass |
| Jump bar reaches each of the five parts and the top; the three story buttons open their module with the cover; coming back lands on the home page; no story left inside a module (desktop 1360 and phone 390) | 36 of 37; the one miss was the test reading the cover 0.25 s after the click, when the Data Backbone had already opened. Watched separately three times: the cover is shown |
| The same, on the host's package versions (Streamlit 1.65, pandas 3.0) | same result |
| Phone, small phone, tablet, tablet on its side (`check_app_mobile.py --pages landing`): errors, sideways scroll, things sticking out, tiny text | 4 of 4 with no fault, after one fix (a layer label stuck out 5 px on the 768 px tablet) |
| Read by eye, desktop and phone, every part | done |
| **After the second pass:** all 35 screens; the same browser test (jump bar, the three Open buttons, coming back) on this PC and on the host's versions; phone and tablet survey 4 of 4; both "More about" rows open and close each other, on desktop and phone | pass. The browser test again scored 36 of 37 on most runs and 37 of 37 on one; each miss was the test looking too soon (the cover already gone, or a long scroll not yet finished), never the same step twice |

## Known, left as they are

- The two module pictures were retaken on 12 October after the day's
  forecast had run. The FloodSense one still shows the local "Run now"
  button, too small to read at the size shown.
- **Soil erosion is named as the next hazard; Assam is not named.** The
  user's decision, 2026-10-12: "Don't mention Assam … just keep soil
  erosion." "More places" shows Arunachal (live) and "Other hill states"
  (planned) only. The same day the user had it taken out of the deck and
  the script too (slide 11's chip, slide 13's "Soil erosion, for Assam",
  the spoken line, one answer and one "words to avoid" row). The internal
  brief (BRIEFING.html/.md) still names it: it carries the plan itself.
- **The company's own site still calls the landslide module SlopeSense**
  and quotes "35.7K mapped failures" on its portfolio card. That is the
  site's to update, not this app's.
- The two product cards stay level because their text is about the same
  length; a much longer line in one would push its button down.
- **Deployed 2026-10-12** to the public app (`v2`, commit `24f7834`), after one
  last fix: the back mountain ridge ended lower than it started, so where
  the backdrop repeats on a wide screen it showed as a cliff. Both ridges
  now end at the height they start.

## Later the same day: two wording rules from the user

- **Never "six rules".** There are more than six, so the page, the deck and
  the script say "rules we keep in mind". The page and slide 5 show six; the
  script adds three (test on ground it has never seen, label every number,
  say so when unsure).
- **The close is general.** "What comes next" names no module and no state:
  more on the same backbone, a loop that runs itself, an open feed. Same
  three on the page's closing block, the deck's slide 13 and in the script.

## After the first deploy (2026-10-12, `df981ac`)

- **The company's mark is in the page's top left corner**, not under the
  title: the bee and "BEE Solutions", a link to the company site. It is
  placed against the scrolling area (`stMain`), so it scrolls away with the
  first screen. Under 1100 px it sits just below the jump bar.
- **"SLOPESENSE" and "Hazard Intelligence Platform" are the same width**
  (239 px each, measured at five screen sizes, on both package sets). The
  title was enlarged to 2 rem and the line under it is stretched to the
  title's width (`text-align-last: justify`), so they stay equal even if a
  font loads differently.
- Checked on the host's versions before the push: home page opens, phone
  and tablet 4 of 4, jump bar and Open buttons 37 of 37.

**Then (`9a03e0d`): the mark floats.** The user wanted it "floating type like the
step bar": it now stays in the top left corner while the page scrolls, in
the same pill as the jump bar. Under 1100 px there is no room beside the
bar, so the bee rides inside the bar as its first item and the corner one is
hidden. (The earlier note above, that it scrolls away, no longer holds.)
Checked on the host's versions: stays put after scrolling at six widths,
never overlaps the bar, phone and tablet 4 of 4, buttons 37 of 37.
