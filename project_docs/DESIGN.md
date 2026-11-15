---
name: Xu hướng chủ đề YouTube
description: Vietnamese YouTube topic trends, presented as a live broadcast desk.
colors:
  broadcast-navy: "#0B1B3A"
  panel-navy: "#12264D"
  selected-navy: "#1A3364"
  track-navy: "#1C3463"
  rule-navy: "#2A4479"
  crawl-navy: "#08142C"
  ink-white: "#FFFFFF"
  ink-steel: "#C5D3EE"
  ink-slate: "#93A8D2"
  breaking-red: "#D41E35"
  breaking-red-deep: "#B9182C"
  clock-gold: "#F5B800"
  series-1-blue: "#3987e5"
  series-2-rust: "#d95926"
  series-3-jade: "#199e70"
  series-4-ochre: "#c98500"
  series-5-rose: "#d55181"
  series-6-green: "#008300"
  series-7-iris: "#9085e9"
  series-other: "#5B6F99"
typography:
  display:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "3.4rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 62"
  headline:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "2rem"
    fontWeight: 800
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 68"
  title:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    letterSpacing: "0.02em"
    fontVariation: "'wdth' 75"
  numeral:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "2.6rem"
    fontWeight: 800
    lineHeight: 1
    fontFeature: "'tnum'"
    fontVariation: "'wdth' 62"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Archivo, Arial Narrow, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 75"
rounded:
  none: "0px"
spacing:
  gutter: "36px"
  gutter-mobile: "16px"
  cell: "16px"
  section: "44px"
components:
  rundown-bar:
    backgroundColor: "{colors.panel-navy}"
    textColor: "{colors.ink-white}"
    rounded: "{rounded.none}"
    height: "64px"
  segment-tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink-steel}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "8.8px 14.4px"
  segment-tab-active:
    backgroundColor: "{colors.ink-white}"
    textColor: "{colors.broadcast-navy}"
    rounded: "{rounded.none}"
  live-bug:
    backgroundColor: "{colors.breaking-red}"
    textColor: "{colors.ink-white}"
    rounded: "{rounded.none}"
    padding: "3.2px 8.8px"
  scoreboard-track:
    backgroundColor: "{colors.track-navy}"
    rounded: "{rounded.none}"
    height: "24px"
  scoreboard-row-selected:
    backgroundColor: "{colors.selected-navy}"
    textColor: "{colors.clock-gold}"
  call-slate:
    backgroundColor: "{colors.selected-navy}"
    textColor: "{colors.ink-white}"
    typography: "{typography.display}"
    rounded: "{rounded.none}"
    padding: "16px 20px 17.6px"
  ticker-tag:
    backgroundColor: "{colors.breaking-red}"
    textColor: "{colors.ink-white}"
    rounded: "{rounded.none}"
    padding: "8.8px 16px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink-white}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "7.2px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.panel-navy}"
  input-text:
    backgroundColor: "{colors.panel-navy}"
    textColor: "{colors.ink-white}"
    rounded: "{rounded.none}"
---

# Design System: Xu hướng chủ đề YouTube

## Overview

**Creative North Star: "The Live Desk"**

The dashboard is a broadcast control desk for Vietnamese YouTube topics. Topics are the stories on the rundown, their share of the conversation is a running scoreboard bar, and bursts are timestamped BREAKING slates and a ticker crawl. It runs on a deep navy ground, carries every heading and number in condensed Archivo caps, and saves its two broadcast signals, red and gold, for the few things that are live. The room should feel like a newsroom graphics package rendered for a projector: dense, ruled, flat, and readable from the back row.

Structure comes from rules, not containers. Lower-third strips sit between a 2px white top rule and a 1px navy hairline. Scoreboard rows are separated by hairlines. Section straps open with a 2px rule. Nothing is rounded, nothing glows, nothing floats. The world refuses the generic analytics grid of KPI cards and chart tiles. Every chart sits directly on the ground and carries a white-ink sentence that reads the data out loud.

The shipped build is Vietnamese-language Streamlit with a Plotly template ("desk") that carries the same ground, ink and categorical slots, so charts and HTML blocks share one world.

**Key Characteristics:**
- Navy ground with tonal navy steps for panel, selected row and empty track; no gray anywhere.
- Archivo variable (wdth 62–125, wght 100–900), self-hosted as base64 woff2, condensed caps for all display, numerals and labels, normal width for reading text.
- Red means "live/bursting", gold means "now/selected". Both stay scarce.
- Seven validated categorical slots fixed to topic size rank; rank 8+ folds to one quiet slate blue.
- Square corners everywhere, including Streamlit widgets and the slider handle.
- Tabular numerals with Vietnamese number formatting (comma decimal, dot thousands).

## Colors

A broadcast navy palette: tonal navy layers, white and blue-tinted ink, two signal colours, and a seven-slot data palette tuned for the dark ground.

### Primary
- **Breaking Red** (breaking-red): the burst signal. Used for the PHÁT LẠI live bug in the rundown, the BREAKING badge on scoreboard rows, the ticker's red top rule and tag, burst pips on the time rail, burst z-score blocks in the burst log, burst-window shading on trend charts (at 0.22–0.3 opacity), and the square scrubber handle. **Breaking Red Deep** (breaking-red-deep) is its hover step, defined for the red primary button.

### Secondary
- **Clock Gold** (clock-gold): "now" and "selected". The live clock, every timestamp (ticker times, burst-log times, keyword hour heads, slider thumb value), the gold now-mark on the time rail and charts, the selected scoreboard label, the analyzer call slate's 4px top rule and its scores, the "MÔ HÌNH CUỐI" tag on the winning experiment row, plus focus ring, text selection and caret.

### Tertiary (categorical data)
- **Series 1–7** (series-1-blue, series-2-rust, series-3-jade, series-4-ochre, series-5-rose, series-6-green, series-7-iris): one per topic, fixed by the topic's size rank in the final model, so a topic keeps its colour on every page. The source palette's red slot is dropped because red belongs to bursts. All seven pass the validator on the navy ground.
- **Other Slate** (series-other): every topic ranked 8 and below ("Khác"), and missing-data bins in the posting-rhythm chart. These topics are identified by their text label alone.

### Neutral
- **Broadcast Navy** (broadcast-navy): page ground, chart paper and plot background.
- **Panel Navy** (panel-navy): rundown bar, text area, select, chart hover label, button hover.
- **Selected Navy** (selected-navy): selected scoreboard row, winning table row, the call slate.
- **Track Navy** (track-navy): empty part of every bar track; disabled buttons.
- **Rule Navy** (rule-navy): every hairline, chart grid and axis line, input border.
- **Crawl Navy** (crawl-navy): the ticker lane, one step darker than the ground so the crawl reads as a separate band.
- **Ink White** (ink-white): headings, numerals, insight sentences, topic names, table cells.
- **Steel Ink** (ink-steel): secondary text (dek, strip captions, inactive tabs, widget labels, chart text), and the analyzer's winning bar when the winner is ranked 8+.
- **Slate Ink** (ink-slate): muted notes, keyword lists, axis ticks, rail ticks (at least 4.5:1 on the ground).

### Named Rules
**The Two Signals Rule.** Red appears only where something bursts or is live; gold only where something is "now" or selected. If a red or gold element doesn't name a burst, a live state, a time or the current selection, it is wrong.

**The No-Gray Rule.** Secondary ink is blue-tinted (Steel, Slate). Neutral gray never appears on the navy ground.

**The Ink-Not-Paint Rule.** Text never wears a series colour. A topic named in a sentence or on a row is white (or gold when selected) bold ink with a square swatch of its colour in front of it.

**The Fixed Slot Rule.** A topic's colour comes from its size rank, never from its position in the current view. Ranks 1–7 get the series slots; rank 8+ is always Other Slate.

## Typography

**Display Font:** Archivo (with Arial Narrow, sans-serif)
**Body Font:** Archivo (with system-ui, sans-serif)

**Character:** One variable family does both jobs. At 62–75% width and weight 700–800 in caps it is broadcast graphics: headlines, scoreboard labels, numerals, slates. At normal width and weight 400 it reads as plain, generous body copy. The font is embedded in the page CSS as base64 woff2 in three unicode-range subsets (Vietnamese, Latin Extended, Latin) with `font-display: block`, so it works offline at the defense.

### Hierarchy
- **Display** (800, 3.4rem / 2.5rem under 720px, line-height 1, wdth 62, uppercase, balanced wrap): one page slug per view. The call slate's verdict uses the same voice at 2.8rem.
- **Headline** (800, 2rem, wdth 68, uppercase): section straps, always opening with a 2px rule above.
- **Title** (700, 1.35rem, wdth 75, uppercase): sub-heads inside a section; scoreboard labels (1.3rem, wdth 70) and burst-log story names share this register.
- **Numeral** (800, 2.6rem, wdth 62, tabular): lower-third strip values and the clock (gold). Scoreboard percentages (1.55rem, wdth 70) and slate times (1.9–2rem, gold) are smaller steps of the same voice.
- **Body** (400, 1.125rem, line-height 1.55): dek (1.25rem, Steel, max 70ch), insight sentences (1.15rem, white, max 75ch), notes (0.98rem, Slate, max 80ch).
- **Label** (700, 1rem, wdth 75, uppercase, 0.04em): segment tabs (1.15rem), widget labels, table heads, buttons. Badges (BREAKING, PHÁT LẠI, table tags) are a tighter 0.8–0.95rem, wdth 75, weight 800, 0.06–0.1em tracking.

### Named Rules
**The Condensed Caps Rule.** Anything that names, counts or times is condensed caps (wdth 62–75) with tabular numerals. Anything that explains is normal-width sentence case.

**The Back-Row Rule.** No reading text below 0.85rem; chart ticks are 15px and chart text 16px. Projector legibility outranks density.

## Layout

A full-bleed broadcast frame. The rundown bar (64px min, Panel Navy, 2px rule beneath) and the segment-tab row bleed edge to edge by cancelling the 36px page gutter. Content runs to a 1680px max width. The top band is: show name and live bug left, segment tabs below, gold clock pinned right behind a vertical hairline, presentation toggle at the tab row's far right.

Content flows as one column of ruled bands: slug and dek, then full-width blocks (scoreboard, strips, charts) separated by straps with 44px top margin. Lower-third strips use an auto-fit grid (min 190px per cell) with vertical hairlines between cells; keyword hour columns use the same pattern at 150px. Scoreboard rows are a four-column grid (label 26% / min 260px, bar, 92px percentage, 84px mover) with keywords on a second line under the bar. On the scoreboard page the ticker is fixed to the bottom edge ("on air") with a 4.5rem spacer.

Under 720px the gutter drops to 16px, scoreboard rows restack to label+percentage over bar+mover, the tab row scrolls horizontally, the ticker stops being fixed, and display/clock sizes step down. Under reduced motion the crawl stops and wraps, the on-air ticker becomes static, and bar transitions are removed.

## Elevation & Depth

Flat. There are no shadows anywhere (the slider handle's default shadow is explicitly removed). Depth is tonal: the ground, a lifted Panel Navy for chrome and inputs, Selected Navy for the selected row and the call slate, a darker Crawl Navy for the ticker band. Hierarchy otherwise comes from rule weight: 4px gold over the call, 2px white over strips, boards and table heads, 2px navy over straps and under the rundown, 1px navy hairlines between rows.

### Named Rules
**The Ruled-Not-Boxed Rule.** Group with rules and tonal steps, never with cards, borders on all four sides, shadows, glow or glass. The only four-sided borders are on inputs, secondary buttons and the void badge.

## Shapes

Square. Every corner is 0px, including Streamlit buttons, text areas, selects, expanders, multiselect tags and the slider handle (a 22px red square). Bars are hard-edged flat fills on a navy track, 24px tall, growing from the left by scaleX. The only round forms are the white dot in the live bug and Streamlit's own toggle. Up/down movers are drawn SVG triangles (12px, Steel up, Slate down), not glyphs. Removed data in the data-quality funnel is shown as a red diagonal hatch, cancelled rather than deleted.

## Components

### Buttons
- **Shape:** square (0px).
- **Secondary (default):** transparent with a Rule Navy 1px border, white condensed caps label (wdth 75, 700, 1.05rem, 0.05em), 7.2px 16px padding. Used for the analyzer's example prompts.
- **Hover / Focus:** border to Steel, background to Panel Navy; focus is the global 3px gold outline at 2px offset.
- **Primary:** Breaking Red fill, white 800 label, hover Breaking Red Deep. Defined but not used in the shipped build.
- **Disabled:** Track Navy fill, Slate label.

### Chips (badges)
- **Live bug / BREAKING:** Breaking Red block, white condensed caps 800, wide tracking. PHÁT LẠI carries a white dot.
- **Table tag:** Clock Gold block with navy ink, marks the winning row.
- **Void:** 2px red outline with pink-red text, marks removed data in the funnel.

### Cards / Containers
- **Corner Style:** none; there are no cards.
- **Background:** the ground, with Selected Navy only for the call slate and selected rows.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** top rules only.
- **Internal Padding:** 16px horizontal in strip cells and slates.

### Inputs / Fields
- **Style:** Panel Navy fill, 1px Rule Navy border, square, white 1.2rem text, gold caret.
- **Focus:** global 3px gold outline.
- **Labels:** condensed caps labels in Steel.

### Navigation
- **Segment tabs:** condensed caps (wdth 75, 700, 1.15rem, 0.04em) in Steel on the ground, square. Hover goes white. The current page is an inverted slab: white fill, navy ink. Under 720px the row scrolls horizontally.

### Scoreboard (signature)
One row per topic, largest first: square swatch and white condensed-caps label, a flat bar in the topic colour on a navy track scaled to the leader, the percentage in condensed tabular numerals, then a mover (drawn triangle plus change in points) and the top keywords in Slate beneath. A selected row gets Selected Navy and a gold label; a bursting topic gets the BREAKING badge. Bars animate with a 0.35s `cubic-bezier(.16,1,.3,1)` ease.

### Time rail and scrubber (signature)
A square red slider handle with a gold thumb value, over a rail of hour ticks in Slate, red pips at each burst peak and a 3px gold now-mark, on the same 0–100% scale as the slider.

### Ticker crawl (signature)
A Crawl Navy band under a 2px red rule. A red BREAKING tag on the left, then a linear crawl of burst items: gold time, white uppercase topic and the numbers. Duration scales with item count (minimum 30s).

### Call slate (analyzer)
Selected Navy block under a 4px gold rule; the called topic in display caps, then a Steel sentence with the gold cosine scores. It reports geometric distance, never probability.

### Lower-third strip, burst log, funnel
The strip is ruled numeral cells. The burst log is a grid row: gold time, the story name and its window, a red z-score block. The funnel shows each cleaning step as a blue kept bar with the removed share hatched in red, with the removed count in pink-red below the kept count.

## Do's and Don'ts

### Do:
- **Do** set every heading, label, numeral and timestamp in condensed Archivo caps (wdth 62–75, weight 700–800) with tabular numerals.
- **Do** colour a topic by its size rank from the seven series slots, and fold rank 8+ to Other Slate.
- **Do** name a topic in white bold ink behind a square swatch of its colour.
- **Do** separate content with 2px and 1px rules and tonal navy steps.
- **Do** keep every corner at 0px, including Streamlit widgets.
- **Do** mark time and selection in Clock Gold, and bursts and live state in Breaking Red.
- **Do** write numbers the Vietnamese way (comma decimal, dot thousands) and follow every chart with a white-ink insight sentence.
- **Do** keep presentation mode on by default: it masks profanity and hides 18+ terms on screen without changing any statistic.

### Don't:
- **Don't** use red or gold for decoration, emphasis or ordinary data series.
- **Don't** set text in a series colour.
- **Don't** introduce gray; secondary ink is Steel or Slate.
- **Don't** add rounded cards, KPI tiles, shadows, glow or glass.
- **Don't** set reading text below 0.85rem or chart text below 15px.
- **Don't** show KMeans output as a probability.
