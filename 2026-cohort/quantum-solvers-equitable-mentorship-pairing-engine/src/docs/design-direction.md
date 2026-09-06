# Braid — Design direction and frontend specification

For the designer to interpret and the frontend engineer to build against. Every value here is a decision, not a suggestion. Where the engineer needs to deviate, they should ask rather than improvise, because most of these values are load-bearing on the ones next to them.

---

## 1. The anchor message

One sentence drives every design decision in this document:

> **You are not the only one in the room.**

That is the emotional problem the product solves. Isolation is the disease; a strand is the treatment. Every screen either delivers on that or gets out of the way.

Three consequences that are not obvious:

1. **The empty state is the most important screen in the product.** A participant signs up in September and gets matched in October. For three weeks the app is empty. If that period feels like abandonment, they churn before the product ever works. The waiting state must feel like being held, not like being forgotten.
2. **The match reveal is the payoff.** It happens once per strand and it is the moment the promise is kept. It gets the entire animation budget.
3. **Scarcity must be visible, not hidden.** When a mentor is at capacity, show them as full rather than removing them from the directory. Hiding scarcity makes the system feel arbitrary. Showing it makes the system feel honest, and honesty is what an equity product is selling.

---

## 2. Principles

**Warm, not soft.** Warmth is in the colour temperature and the copy, not in rounded-everything and pastel-everything. The interface is confident and legible. It does not coo.

**Unity is structural, not decorative.** The weave shows up in the mark, in the match reveal, and in the strand header. It does not show up as background pattern on every page. Repeating a metaphor everywhere kills it.

**One bold thing per screen.** Everything else is quiet. If two elements are competing for attention, one of them is wrong.

**Motion explains, never entertains.** Every transition answers "where did this come from" or "where did this go". If it answers neither, delete it.

**Density is respect.** Coordinators are doing real work with real deadlines. Tables should be dense and scannable. Do not make a coordinator scroll through cards to review 200 applications.

---

## 3. Identity

### 3.1 The mark

**The weave.** Four rounded bars, two horizontal and two vertical, in a strict alternating over-under. No beginning, no end, no hierarchy between the strands. It reads as a woven square at any size and it survives every reproduction test the gradient loop fails.

**Construction.** On a 140 unit square with the mark occupying the central 100 units:

- Horizontal bars: 100 long, 16 thick, fully rounded ends, centred at 45 and 85 on the vertical axis.
- Vertical bars: identical, centred at 45 and 85 on the horizontal axis.
- Weave order: top horizontal passes over the right vertical and under the left vertical. Bottom horizontal passes over the left vertical and under the right vertical. This is the only correct alternation. Getting it wrong produces a lattice, not a weave, and the difference is visible even to people who cannot name it.
- Colour assignment: top horizontal fuchsia, bottom horizontal jade, left vertical marigold, right vertical ink.

**Clear space.** 20 units on all sides, which is the bar thickness plus 25 percent. Never place the mark inside a coloured tile. It floats on paper or on ink.

**Sizes.** Full colour at 32px and above. Single colour below 32px, with the weave gaps preserved because the gaps are the mark. At 16px, thicken the bars to 18 units and reduce the gaps proportionally so the favicon does not turn to mush.

**Never.** Do not rotate it. Do not add a gradient. Do not animate it as a permanent loop. Do not place it on a photograph. Do not outline it.

### 3.2 The wordmark

Set in the display face, weight 500, tracking minus 2 percent, lowercase descender of the "d" aligned to the mark's baseline. Lockup: mark, then a gap equal to the mark's bar thickness, then the wordmark at a cap height equal to 60 percent of the mark height.

Vertical lockup for narrow contexts. Mark alone for the app icon, favicon, and any surface under 120px wide.

### 3.3 App icon

The mark in full colour on paper, not on ink. Every other app on the phone is a dark tile with a bright glyph. A warm off-white tile with a woven mark will be the only light thing on the screen, and that is worth more than any amount of gradient.

---

## 4. Colour

### 4.1 Brand

|Token|Hex|Role|
|---|---|---|
|`--ink`|`#241733`|Primary text, borders at strength, the fourth strand|
|`--fuchsia`|`#D6246E`|Primary action, first strand|
|`--marigold`|`#FFB627`|Emphasis, highlight, second strand|
|`--jade`|`#0FA37F`|Success, third strand|
|`--paper`|`#FFFCF7`|Page background|
|`--line`|`#E8DFD6`|Hairlines and dividers|

The palette is drawn from thread and bead colours, not from software convention. It is warm and bright without landing on the terracotta-and-cream default that every product deck currently uses.

### 4.2 Full ramps

```
ink       50 #F4F1F7   100 #DDD5E4   200 #B9AAC6   400 #6B5580   600 #402C57   800 #241733   900 #150C1F
fuchsia   50 #FDEBF2   100 #F9C4DA   200 #F296B8   400 #E4548E   600 #D6246E   800 #A11550   900 #6B0C34
marigold  50 #FFF6E3   100 #FFE5AC   200 #FFD26F   400 #FFB627   600 #C88709   800 #8F5F04   900 #5C3C02
jade      50 #E6F7F1   100 #A9E5D0   200 #6DD1B0   400 #1CBB90   600 #0FA37F   800 #0A7059   900 #054636
warm      50 #FFFCF7   100 #F7F1E9   200 #E8DFD6   400 #948A81   600 #7B6C60   800 #574A3F   900 #33291F
```

### 4.3 Semantic tokens

The engineer never writes a brand hex in a component. Components consume semantic tokens only.

```
--bg-page             warm-50
--bg-surface          #FFFFFF
--bg-sunken           warm-100
--bg-inverse          ink-800

--text-primary        ink-800
--text-secondary      warm-800
--text-muted          warm-600
--text-inverse        warm-50
--text-link           fuchsia-800

--border-subtle       warm-200
--border-default      warm-400
--border-strong       ink-400

--action-primary-bg   fuchsia-600
--action-primary-fg   #FFFFFF
--action-primary-hover fuchsia-800

--focus-ring          fuchsia-600
--focus-ring-offset   bg-page

--status-success      jade-600
--status-success-text jade-800
--status-warning      marigold-800
--status-danger       #C42B1C
--status-info         ink-600

--strand-1            fuchsia-600
--strand-2            marigold-400
--strand-3            jade-600
```

### 4.4 Rules

- **The three strand colours appear in exactly three places:** the mark, the match reveal, and participant identity chips. Nowhere else. This is what keeps them meaningful.
- **Marigold never carries white text.** Its only text partner is ink. This is non-negotiable and it is why marigold is an emphasis colour, not an action colour.
- **Fuchsia at 600 carries white text and passes AA at normal size.** For fuchsia _as_ text on paper, use fuchsia-800.
- **Jade at 600 is a fill, not text, and it never carries white.** On paper it measures 3.20:1, and white on it measures 3.20:1 — both fail AA. Jade-600 takes ink text (5.27:1), exactly as marigold does. For jade _as_ text, use jade-800 via `--status-success-text` (6.04:1 on paper). A jade fill that must carry white text uses jade-800 (6.04:1). `--strand-3` stays at 600, because it is a fill.
- **Warm-400 and warm-600 are set by contrast, not by taste.** `--border-default` bounds interactive controls and must clear 3:1; `--text-muted` carries helper text at 12px and must clear 4.5:1. `--border-subtle` is a decorative hairline on cards and dividers, carries no meaning alone, and is deliberately left light.
- **Health signals do not use red, amber, green.** A quiet strand is not an error, and a coordinator reading a wall of red will stop reading. Use ink weight and a small textual state instead: bold ink for needs attention, muted for fine.
- **One accent per screen.** If a page has a primary action, nothing else on it is fuchsia.

### 4.5 Dark mode

Not a launch requirement, but token names must be built to support it from day one. When it arrives: `--bg-page` becomes ink-900, `--bg-surface` becomes ink-800, `--text-primary` becomes warm-100, and the strand colours shift up one stop to 400 for luminance. Nothing else changes.

---

## 5. Typography

### 5.1 Faces

|Role|Face|Source|Weights|
|---|---|---|---|
|UI and body|**Switzer**|Fontshare, self-hosted|400, 500, 600|
|Display|**Gambetta**|Fontshare, self-hosted|500, 600|
|Data|**JetBrains Mono**|self-hosted|400, 500|

Switzer is a warm-neutral variable grotesque that holds up at 13px in a dense table, which Inter also does, but Switzer has slightly humanist terminals that keep the interface from reading as a generic dashboard.

Gambetta is a variable serif with calligraphic contrast. It carries warmth and it carries a voice. It is used **only** for the anchor moments listed below. It never appears in a table, a form label, or a button.

JetBrains Mono is for match scores, participant counts, coverage percentages, and IDs. Numbers that are compared vertically must be tabular.

Self-host everything. Preload the two weights used above the fold. A participant on a Lagos mobile network should not wait on a font CDN.

### 5.2 Where the display face is allowed

Exactly five places. Adding a sixth requires a conversation.

1. The onboarding welcome headline.
2. The empty state on Home before matching.
3. The match reveal headline.
4. The report cover page.
5. Marketing and the program landing page hero.

Everywhere else is Switzer. The restraint is what makes it land when it does appear.

### 5.3 Scale

Base 16px, ratio 1.25, rounded to whole pixels. Thirteen tokens.

|Token|Size / line height|Face|Use|
|---|---|---|---|
|`display-xl`|56 / 60, tracking -2%|Gambetta 500|Landing hero, match reveal|
|`display-l`|40 / 46, tracking -1.5%|Gambetta 500|Onboarding, empty state|
|`heading-l`|28 / 36|Switzer 600|Page titles|
|`heading-m`|22 / 30|Switzer 600|Section headings|
|`heading-s`|18 / 26|Switzer 600|Card titles|
|`body-l`|17 / 28|Switzer 400|Long-form reading, strand messages|
|`body-m`|15 / 24|Switzer 400|Default UI text|
|`body-s`|13 / 20|Switzer 400|Table cells, dense lists|
|`label`|13 / 16, tracking 2%, uppercase|Switzer 600|Form labels, eyebrows, table headers|
|`caption`|12 / 18|Switzer 400|Helper text, timestamps|
|`data-m`|15 / 20, tabular|JetBrains Mono 500|Scores, counts, percentages|
|`data-l`|40 / 46, tracking -1.5%, tabular|JetBrains Mono 500|Live counts at display size, narrow|
|`data-xl`|56 / 60, tracking -2%, tabular|JetBrains Mono 500|Landing hero counts, match reveal|

`data-l` and `data-xl` share their metrics with `display-l` and `display-xl` so a mono number and a Gambetta line sit on one baseline grid. They exist because section 9 puts live counts at display size in the mono face, in the landing hero and again in the match reveal, and the mono axis had only one step. Numbers only. A word never takes them.

**Rules.** Never more than three sizes in one view. Body copy caps at 68 characters per line. Sentence case everywhere except the `label` token. No italics except in a quoted participant response, where the quote is the participant's own words and the italic marks it as theirs.

---

## 6. Space, shape, and depth

**Space scale**, 4px base: 4, 8, 12, 16, 24, 32, 48, 64, 96. Nothing between.

**Grid.** 12 columns, 24px gutter, 1200px max for the coordinator shell, 900px for the participant shell, 720px for public pages. Below 768px everything is a single column with 16px margins.

**Radius.** `--radius-xs` 3px for controls under 24px, `--radius-sm` 6px for inputs and chips, `--radius-md` 10px for cards and buttons, `--radius-lg` 16px for modals and the strand panel. The mark's bars are fully rounded and that is the only fully rounded shape in the system apart from avatars.

`--radius-xs` exists for one reason: a checkbox is 16px, and 6px on a 16px box is 37 percent of the width, which reads as a circle. Shape is what separates a checkbox from a radio before either is clicked — the tick and the dot only arrive afterwards — so the smaller box needs the smaller radius. Do not reach for it above 24px. Anything larger is an input and takes 6px.

**Borders.** 1px, `--border-subtle` by default. The interface is defined by hairlines and space, not by shadows.

**Depth.** Two levels only.

- `--shadow-raised`: `0 1px 2px rgba(36,23,51,0.06), 0 4px 12px rgba(36,23,51,0.04)` for dropdowns, popovers, toasts.
- `--shadow-overlay`: `0 8px 32px rgba(36,23,51,0.12)` for modals only.

Cards do not have shadows. Cards have a border. A page of shadowed cards looks like a template.

---

## 7. Motion

### 7.1 Tokens

```
--dur-instant   90ms    hover, focus, colour change
--dur-quick     160ms   dropdown, tooltip, checkbox, toast in
--dur-base      240ms   panel, drawer, modal, page section
--dur-slow      420ms   route transition, list reflow
--dur-moment    1400ms  the match reveal, once

--ease-out      cubic-bezier(0.22, 1, 0.36, 1)     entering, expanding
--ease-in       cubic-bezier(0.64, 0, 0.78, 0)     exiting, collapsing
--ease-inout    cubic-bezier(0.65, 0, 0.35, 1)     moving between two positions
--ease-weave    cubic-bezier(0.34, 0.9, 0.28, 1)   the signature curve, strand motion only
```

Animate `transform` and `opacity` only. Never animate `height`, `top`, `width`, or `box-shadow`. For height changes use a grid-rows transition or FLIP.

### 7.2 Named transitions

|Name|Where|Behaviour|
|---|---|---|
|**Settle**|Any list or card entering|Fade in with 8px upward translate, `--dur-quick`, `--ease-out`. Stagger 40ms per item, capped at 6 items total stagger.|
|**Lift**|Card and row hover|Border darkens to `--border-default` over `--dur-instant`. No translate, no scale, no shadow.|
|**Slide-over**|Drawers, strand panel on mobile|Translate from edge, `--dur-base`, `--ease-out`. Backdrop fades at half the duration.|
|**Cross**|Route change within a shell|Outgoing fades over 90ms, incoming settles over 160ms, no horizontal movement. Route transitions that slide make the app feel slow.|
|**Count**|Any number that changes on the dashboard|Tween the digits over `--dur-base`. Tabular figures make this legible.|
|**Weave**|The signature. Defined below.||

### 7.3 The signature moment: the match reveal

This fires once per strand, the first time a participant opens a newly published strand. Not on every visit. It is the emotional payoff of the entire product and it is the only place in the interface allowed to take more than half a second.

**Sequence, 1400ms total:**

1. **0 to 300ms.** The screen holds two vertical strands, separated, one on each side. Each carries a participant's avatar and name. Strand colours are `--strand-1` and `--strand-2`. Nothing else is on screen.
2. **300 to 900ms.** The strands travel toward each other and cross once, over-under, on `--ease-weave`. The crossing is the mark's geometry, animated. They do not merge into one line. They stay two distinct strands that now hold together. That distinction is the whole point: mentoring is not absorption.
3. **900 to 1150ms.** The display-l headline settles in beneath the weave. Copy: **"You've been matched with Amara."** Name, not role.
4. **1150 to 1400ms.** The strand detail page settles in behind, and a single primary action appears: **Say hello.** One action. Not three.

**Constraints.** Skippable by tap or key at any point. Never replayed. Under `prefers-reduced-motion`, the two strands appear already crossed with a 160ms fade, headline and action follow immediately, and no motion occurs. The reduced-motion version must still feel like a moment, which means the composition carries it, not the animation.

**Group strands** use three strands crossing rather than two, and the headline names the group.

### 7.4 What we will not animate

Page loads. Numbers on tables. Modal backdrops beyond a fade. Anything on the coordinator side except toasts and the run progress bar. Coordinators are working, not being delighted.

### 7.5 Reduced motion

Respect `prefers-reduced-motion: reduce` globally. Under it: all durations collapse to `--dur-instant`, all translate distances go to zero, stagger goes to zero, the match reveal degrades as described above. Nothing becomes unusable and nothing disappears.

---

## 8. Component specifications

Only the components that carry the product. Everything else follows from the tokens.

### 8.0 Disabled and loading, shared by every control

**Disabled.** Text `--text-muted`. Controls that normally carry a fill take `--bg-sunken`; bordered controls take `--border-subtle`; text-only controls take neither. Cursor `not-allowed`. No hover response and no press response. Disabled text is exempt from the contrast floor in section 11, because it is not an active control.

**Loading is not disabled.** A loading control keeps its variant colour, because greying it out reads as "you cannot do this" when the truth is "this is happening". It blocks input, preserves its width so nothing reflows, and announces what is in progress to a screen reader. Say what is happening — "Publishing", not "Loading".

### 8.1 Button

Heights 40 (default), 32 (compact, tables), 48 (primary CTA on mobile). Horizontal padding 16, 12, 20. `--radius-md`.

- **Primary:** fuchsia-600 fill, white text, hover fuchsia-800, active scale 0.98 over 90ms.
- **Secondary:** transparent fill, `--border-default` border, ink text, hover border `--border-strong`.
- **Ghost:** text only, hover `--bg-sunken`.
- **Danger:** only for irreversible destructive actions, and only inside a confirmation dialog.

Focus ring: 2px `--focus-ring`, 2px offset, always visible on keyboard focus, never suppressed. Loading state replaces the label with a spinner and preserves the button width so nothing reflows.

Label rule: the verb on the button is the verb in the resulting toast. "Publish" produces "Published."

### 8.2 Form field

Label above, 8px gap, `label` token. Input 44px tall, 12px horizontal padding, `--radius-sm`, `--border-default`. Focus: border becomes fuchsia-600 plus 3px fuchsia-50 ring. Helper text below in `caption`, `--text-muted`.

Error state: border `--status-danger`, message below in `--status-danger` with a 12px icon. Errors say what went wrong and how to fix it. "Enter a date after 14 September" not "Invalid input."

Required fields are marked. Optional fields are not. Whichever is rarer gets the mark.

### 8.3 Strand card

The most-seen component in the participant shell.

Border, no shadow, `--radius-md`, 16px padding. Avatar 40px, name in `heading-s`, role chip in the partner's strand colour at 12 percent opacity with the 800 stop as text. Last message preview in `body-s` `--text-secondary`, truncated to one line. Right side: unread count as a fuchsia pill with a number, or the next session time in `data-m`. One or the other, never both — an unread strand shows its count, and the session waits until the messages have been read.

Whole card is the link and one tab stop. Hover darkens the border from `--border-subtle` to `--border-default` over `--dur-instant`. No lift, no shadow.

Quiet state: after 14 days with no activity, a muted line replaces the preview and reads "Quiet for 3 weeks." Not red. Not an alert icon. A fact, stated plainly. Whole weeks, floored, up to eight; past that, whole months.

Ended state: the same muted line, reading "Ended 1 July." The avatar and the chip drop the strand colour for `--bg-sunken` with `--text-secondary`, 7.62:1. No pill, no session.

Group: up to three avatars overlapping by 12, all member names truncated to one line, and a neutral chip reading "Group of 5" that counts the reader too. No single partner owns the colour, so the chip does not take one.

Strand colour is chosen from the partner's participation id, not from their position in the list, so a person is the same colour on every screen and a re-sort does not reshuffle the page.

**The avatar takes the 900 stop, not the 800.** The chip and the avatar are tinted from the same ramp but at different depths, and only the chip's 12 percent tint is light enough to carry 800 text. Measured on `--bg-surface`:

| | fuchsia | marigold | jade |
|---|---|---|---|
| chip: 800 on the base at 12% | 6.39:1 | 5.14:1 | 5.30:1 |
| avatar: 800 on the 100 stop | 5.09:1 | **4.48:1** | **4.26:1** |
| avatar: 900 on the 100 stop | 8.07:1 | 8.11:1 | 7.65:1 |

Two of the three fail at 800 against the 4.5:1 floor in section 11. Lightening the avatar background instead would pass, but would leave the avatar and the chip nearly the same colour and lose the depth that makes them read as one identity unit. So the background stays at 100 and the initials go to 900. Do not put the 800 values back.

### 8.4 Data table

The coordinator side is mostly this component.

Row height 48. Header row `label` token, `--bg-sunken`, sticky. Cells `body-s`. Zebra striping off; hairline row borders on. Numeric columns right-aligned in `data-m`. Sortable headers show direction on hover before click.

Bulk select: checkbox column, and when any row is selected the header row is replaced by an action bar showing the count and available actions. Do not float a separate toolbar.

Every table has a filter bar above it and a row count below it. Every table exports to CSV.

### 8.5 Empty state

The component that decides whether someone comes back.

Composition: the weave mark at 48px in `--border-default`, a `display-l` line, one sentence of `body-m` explaining what will fill this space and when, and either one action or nothing at all. Never an illustration of a person, never a shrug, never "Nothing here yet."

Home before matching reads:

> **Matching opens 14 September.** Twelve mentors have joined so far. Finish your profile before then and you'll be included in the first round.

That copy does three things at once: it sets a date, it shows the person they are part of something already populated, and it gives them one useful action.

### 8.6 Run progress

Publishing a matching run is slow and irreversible. It gets a determinate progress bar, a live count of strands created, and no cancel button once it has started, because a half-published run is worse than a slow one. On completion, the page transitions to the published state directly. No success modal.

---

## 9. Screen-level direction

Six screens set the tone for the other thirty-nine.

**Program landing.** Full-bleed `display-xl` headline. The hero is not a stock photo and not a gradient. It is a live count: how many mentors have joined, how many places remain, how many days until applications close. Real numbers, set in the mono face, at display size. Nothing else competes. One button.

**Application form.** One question per view on mobile, one section per view on desktop. Progress shown as sections completed, never as a percentage, because a percentage on a form the coordinator built is a lie. Autosave indicator is a small timestamp, not a spinner. The form must feel finishable, which means never showing the applicant how many questions remain until they are within the last section.

**Onboarding.** Full-bleed, `display-l`, four cards, one idea each. This is the only place the brand may be loud. Ends with the code of conduct and a single accept.

**Home.** One next-action card at the top, sized larger than anything below it. Strands below. Everything else is secondary. If there is no next action, say so plainly rather than inventing one.

**Strand detail.** Two columns on desktop at 380 and 520. The conversation is the wider one. On mobile the conversation is the page and the partner card collapses to a header that expands on tap. The "why you were matched" line sits directly under the partner's name in `body-s`, always visible, never behind a disclosure. Participants should not have to hunt for the reason they are talking to this person.

**Run review.** The fairness summary sits above the pair list, full width, always. A coordinator must see coverage, load spread, and the quality gap between priority bands before she sees a single name. Putting the pairs first would train her to optimise pair by pair, which is precisely the behaviour the product exists to prevent. This is a design decision with an ethical payload and it should not be reordered for convenience.

---

## 10. Voice

Plain, warm, direct. Nigerian English is fine and preferred over transatlantic neutral. Short sentences.

- Name people, not roles. "You've been matched with Amara" beats "Your mentor has been assigned."
- Active voice, always. "Publish 42 strands" not "Strands will be published."
- Errors do not apologise and are never vague. "That invitation expired on 3 August. We've told Ngozi you tried to join."
- Empty states are invitations, not admissions.
- Never say "Oops."
- Never use exclamation marks in system messages. The product is warm through what it says, not through punctuation.

---

## 11. Accessibility floor

Not optional and not a phase two. This is a Goal 5 product and the argument makes itself.

- Contrast: 4.5:1 for text under 18px, 3:1 for larger text and interface borders. Marigold on white fails and is therefore never text.
- Every interactive element reachable by keyboard, in visible order, with a visible focus ring. Never `outline: none` without a replacement.
- Modals trap focus and return it to the trigger on close.
- Every input has a programmatically associated label. Placeholder is never the label.
- Live regions announce toasts, unread counts, and run progress.
- Colour never carries meaning alone. Every strand colour is paired with a name. Every status colour is paired with text.
- Touch targets 44px minimum.
- Test with the keyboard only, once per screen, before it ships.

---

## 12. Anti-patterns

Things that would make this look like every other product, listed so nobody has to relitigate them.

Gradient buttons. Glassmorphism. Shadowed cards in a grid. Illustration sets of people with no faces. Emoji in system copy. Skeleton screens that do not match the shape of the content that follows. Toast notifications for successful reads. Modals that could have been pages. A dashboard of four stat tiles with percentage change arrows. Loading spinners longer than 400ms without a determinate indicator. Confetti.

---

## 13. Handoff

**The designer delivers:** the mark in SVG at three sizes and two colourways; a token file matching section 4, 5, 6, and 7 exactly; the six screens in section 9 at 1280 and 390; every component in section 8 in all its states including empty, loading, error, and disabled; and a motion prototype of the match reveal.

**The engineer delivers:** a `tokens.css` file containing every value in this document as a custom property, with no hex value appearing anywhere else in the codebase; the component library from section 8 with each state reachable in isolation; and the shell layer from the overview doc.

**Definition of done for any screen:** it works at 390px wide, it is fully keyboard operable with visible focus, it respects reduced motion, its empty and loading and error states exist and have been seen, its copy follows section 10, and no value in it was invented outside this document.

**Order of work.** Tokens first. Then the four components that appear everywhere: button, form field, data table, empty state. Then the strand card. Then the screens. The match reveal is built last, when the product it pays off actually exists.