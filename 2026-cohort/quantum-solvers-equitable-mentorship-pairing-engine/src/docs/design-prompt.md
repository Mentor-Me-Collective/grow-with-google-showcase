You are designing the frontend of **Braid**, a mentoring platform. Work as a senior product designer with a clear point of view. Every value below is a decision, not a suggestion. Do not substitute your own palette, typefaces, or spacing. Do not add anything not asked for.

---

## The product

Organisations run structured mentoring programs. An organisation owns many programs; each program has its own application form, matching rules, roster and report. Inside a program, a mentoring relationship is called a **strand**, either one to one or a group.

Two audiences with opposite needs:

- **Participants** (mentees and mentors). Global, and mostly on phones. Design mobile-first and treat performance as a baseline standard, not a concession: fast first paint, self-hosted fonts, no layout shift. They need warmth, clarity and one obvious next action.
- **Coordinators.** On desktop, doing real work against deadlines. They need density, tables and speed. Do not make them scroll cards.

Same account, different role per program. A woman can be a mentor in one program and a mentee in another.

## The anchor message

> **You are not the only one in the room.**

Isolation is the problem; a strand is the answer. Three consequences that must show in the work:

1. **The empty state is the most important screen.** Someone applies in September and gets matched in October. For weeks the app is empty. That waiting must feel like being held, not forgotten.
2. **The match reveal is the payoff.** It happens once per strand. It gets the entire animation budget.
3. **Scarcity is shown, not hidden.** A mentor at capacity appears as full, never removed from the directory. Honesty is what the product sells.

---

## The mark

Build it, do not import it. **A woven square.** Four rounded bars in strict alternating over-under.

- Canvas 140 units. Mark occupies the central 100.
- Two horizontal bars, 100 long and 16 thick, fully rounded ends, centred at y=45 and y=85.
- Two vertical bars, identical, centred at x=45 and x=85.
- Weave: top horizontal passes **over** the right vertical and **under** the left vertical. Bottom horizontal passes **over** the left vertical and **under** the right vertical. This alternation is the mark. Get it wrong and it is a lattice, not a weave.
- Colours: top horizontal fuchsia, bottom horizontal jade, left vertical marigold, right vertical ink.
- Clear space 20 units all sides. Never inside a coloured tile. Never rotated, gradiented, outlined, or on a photograph.
- Single colour version below 32px, gaps preserved.
- App icon: full colour mark on paper, not on ink. A light tile is the point.

Wordmark "Braid" in the display face, weight 500, tracking -2%, cap height at 60% of mark height, gap between mark and word equal to one bar thickness.

---

## Colour

Brand:

```
ink       #241733
fuchsia   #D6246E
marigold  #FFB627
jade      #0FA37F
paper     #FFFCF7
line      #E8DFD6
```

Ramps:

```
ink       50 #F4F1F7  100 #DDD5E4  200 #B9AAC6  400 #6B5580  600 #402C57  800 #241733  900 #150C1F
fuchsia   50 #FDEBF2  100 #F9C4DA  200 #F296B8  400 #E4548E  600 #D6246E  800 #A11550  900 #6B0C34
marigold  50 #FFF6E3  100 #FFE5AC  200 #FFD26F  400 #FFB627  600 #C88709  800 #8F5F04  900 #5C3C02
jade      50 #E6F7F1  100 #A9E5D0  200 #6DD1B0  400 #1CBB90  600 #0FA37F  800 #0A7059  900 #054636
warm      50 #FFFCF7  100 #F7F1E9  200 #E8DFD6  400 #948A81  600 #7B6C60  800 #574A3F  900 #33291F
```

Semantic mapping. Components reference these names, never raw hex:

```
bg-page warm-50 | bg-surface #FFFFFF | bg-sunken warm-100 | bg-inverse ink-800
text-primary ink-800 | text-secondary warm-800 | text-muted warm-600 | text-inverse warm-50 | text-link fuchsia-800
border-subtle warm-200 | border-default warm-400 | border-strong ink-400
action-primary-bg fuchsia-600 | action-primary-fg #FFFFFF | action-primary-hover fuchsia-800
focus-ring fuchsia-600
status-success jade-600 | status-success-text jade-800 | status-warning marigold-800 | status-danger #C42B1C | status-info ink-600
strand-1 fuchsia-600 | strand-2 marigold-400 | strand-3 jade-600
```

Hard rules:

- The three strand colours appear in exactly three places: the mark, the match reveal, and participant identity. Identity means the avatar and the role chip together, on the same person, in the same colour. Nowhere else.
- A strand colour is chosen from the person's participation id, so it does not change when a list is re-sorted.
- Marigold never carries white text. Its only text partner is ink.
- Fuchsia as text on paper uses fuchsia-800. Fuchsia-600 is for fills with white text.
- Health signals never use red, amber, green. A quiet strand is not an error. Use ink weight plus plain words.
- One accent per screen. If a page has a primary action, nothing else on it is fuchsia.
- Light mode only for now, but name every colour semantically so dark mode is a token swap later.

---

## Typography

- **Switzer** for all UI and body. Weights 400, 500, 600.
- **Gambetta** for display only.
- **JetBrains Mono** for scores, counts, percentages, IDs. Tabular figures.

Gambetta is allowed in exactly five places: the onboarding headline, the Home empty state, the match reveal headline, the report cover, and the landing hero. Nowhere else. Never in a table, a label, or a button. The restraint is what makes it land.

Scale:

```
display-xl  56/60  -2%    Gambetta 500   landing hero, match reveal
display-l   40/46  -1.5%  Gambetta 500   onboarding, empty state
heading-l   28/36         Switzer 600    page titles
heading-m   22/30         Switzer 600    section headings
heading-s   18/26         Switzer 600    card titles
body-l      17/28         Switzer 400    strand messages, long reading
body-m      15/24         Switzer 400    default UI
body-s      13/20         Switzer 400    table cells, dense lists
label       13/16  +2% uppercase  Switzer 600   form labels, eyebrows, table headers
caption     12/18         Switzer 400    helper text, timestamps
data-m      15/20         JetBrains Mono 500   numbers
```

Never more than three sizes in one view. Body copy caps at 68 characters per line. Sentence case everywhere except `label`. No italics except a quoted participant answer, where italic marks it as their own words.

---

## Space, shape, depth

- Space scale, 4px base: 4, 8, 12, 16, 24, 32, 48, 64, 96. Nothing between.
- Grid: 12 columns, 24px gutter. Max width 1200 coordinator, 900 participant, 720 public. Below 768px, single column, 16px margins.
- Radius: 3px controls under 24px, 6px inputs and chips, 10px cards and buttons, 16px modals and the strand panel. Fully rounded only for the mark's bars and avatars.
- The 3px step is for checkboxes and nothing else reaches for it. At 16px a 6px radius reads as a circle, and shape is what separates a checkbox from a radio before either is clicked.
- Borders: 1px, border-subtle by default. The interface is defined by hairlines and space.
- Depth, two levels only. Raised: `0 1px 2px rgba(36,23,51,0.06), 0 4px 12px rgba(36,23,51,0.04)` for dropdowns, popovers, toasts. Overlay: `0 8px 32px rgba(36,23,51,0.12)` for modals.
- **Cards have a border, never a shadow.** A page of shadowed cards looks like a template.

---

## Motion

```
dur-instant  90ms    hover, focus, colour
dur-quick    160ms   dropdown, tooltip, toast
dur-base     240ms   panel, drawer, modal
dur-slow     420ms   route change, list reflow
dur-moment   1400ms  the match reveal, once

ease-out     cubic-bezier(0.22, 1, 0.36, 1)
ease-in      cubic-bezier(0.64, 0, 0.78, 0)
ease-inout   cubic-bezier(0.65, 0, 0.35, 1)
ease-weave   cubic-bezier(0.34, 0.9, 0.28, 1)   strand motion only
```

Transform and opacity only. Named transitions:

- **Settle.** Lists and cards entering: fade with 8px upward translate, dur-quick, ease-out, 40ms stagger capped at 6 items.
- **Lift.** Row and card hover: border darkens to border-default over dur-instant. No translate, no scale, no shadow.
- **Cross.** Route change: outgoing fades 90ms, incoming settles 160ms, no horizontal movement.
- **Count.** Dashboard numbers tween over dur-base in tabular figures.

Do not animate: page loads, table numbers, anything on the coordinator side except toasts and the run progress bar.

### The signature moment: the match reveal

Fires once per strand, the first time a participant opens a newly published one. 1400ms total.

1. **0 to 300ms.** Two vertical strands, separated, one each side, each carrying an avatar and a name. Colours strand-1 and strand-2. Nothing else on screen.
2. **300 to 900ms.** They travel toward each other and cross once, over-under, on ease-weave. The crossing is the mark's geometry animated. **They do not merge into one line.** They stay two distinct strands that now hold together. Mentoring is not absorption, and the animation must say that.
3. **900 to 1150ms.** Headline settles in beneath, display-l: "You've been matched with Amara." Name, not role.
4. **1150 to 1400ms.** The strand page settles in behind and one action appears: **Say hello.** One. Not three.

Skippable by tap or key. Never replayed. Under reduced motion the strands appear already crossed with a 160ms fade and everything follows immediately, and the composition alone still has to carry the moment.

---

## Components to design

Every state: default, hover, focus, active, disabled, loading, error, empty.

1. **Button.** Heights 40 default, 32 compact, 48 mobile CTA. Padding 16 / 12 / 20. Primary fuchsia-600 fill with white text. Secondary transparent with border-default. Ghost text only. Danger only inside confirmation dialogs. Focus ring 2px fuchsia-600, 2px offset, never suppressed. Loading replaces the label with a spinner and preserves width.
2. **Form field.** Label above at 8px gap in the `label` token. Input 44px tall, 12px horizontal padding, radius 6. Focus: fuchsia-600 border plus 3px fuchsia-50 ring. Helper text in caption. Error state with a message that says what to do: "Enter a date after 14 September", never "Invalid input". Mark whichever is rarer, required or optional, not both.
3. **Strand card.** Border, no shadow, radius 10, 16px padding. Whole card is the link. Hover darkens the border to border-default; no lift, no shadow. 40px avatar on the 100 stop of the partner's strand colour with the **900** stop as initials — the 800 stop measures 4.48:1 on marigold and 4.26:1 on jade and must not be used here. Name in heading-s. Role chip in the same colour at 12% opacity with the 800 stop as text, which does pass. One-line message preview in body-s. Right side: unread count as a fuchsia pill with a number, **or** next session in data-m, never both. Quiet state after 14 days replaces the preview with "Quiet for 3 weeks" in muted ink. Not red. Not an alert icon. Ended replaces it with "Ended 1 July" and drops the strand colour for bg-sunken. Group: three avatars overlapping by 12, names truncated to one line, neutral chip reading "Group of 5".
4. **Data table.** Row height 48. Sticky header in the `label` token on bg-sunken. Cells in body-s. No zebra striping, hairline row borders. Numbers right-aligned in data-m. On bulk select the header row is replaced by an action bar with the count. Filter bar above, row count below.
5. **Empty state.** Weave mark at 48px in border-default, a display-l line, one sentence of body-m saying what will fill this and when, then one action or none. Never an illustration of a faceless person. Never "Nothing here yet."
6. **Weave mark** at 16, 32, 48 and 96px, full colour and single colour.

---

## Screens to design

Each at **1280** and **390** wide.

1. **Program landing (public).** The hero is not a photo and not a gradient. It is live numbers set in JetBrains Mono at display size: mentors joined, places remaining, days until applications close. One display-xl headline. One button. Nothing competes.
2. **Application form (public).** One section per view on desktop, one question per view on mobile. Progress as sections completed, never a percentage. Autosave shown as a small timestamp, not a spinner. Do not reveal how many questions remain until the last section, so the form feels finishable.
3. **Home, participant, empty state.** The one that matters. Weave mark, display-l reading "Matching opens 14 September", then: "Twelve mentors have joined so far. Finish your profile before then and you'll be included in the first round." One action.
4. **Home, participant, populated.** One next-action card at the top, visibly larger than everything under it. Strand cards below. If there is no next action, say so plainly rather than inventing one.
5. **Strand detail.** Desktop two columns at 380 and 520, conversation is the wider one. Mobile: conversation is the page, partner card collapses into a header that expands on tap. The "why you were matched" line sits directly under the partner's name in body-s, always visible, never behind a disclosure.
6. **Match reveal.** All four frames of the sequence above.
7. **Coordinator dashboard.** Desktop only. Left sidebar with program selector at top, then grouped nav: Overview, Setup, People, Matching, Running, Insight. Content is program health plus an attention list of things needing a human, each linking to the page that resolves it.
8. **Run review.** Desktop only, and the layout carries an ethical decision. **The fairness summary sits above the pair list, full width, always:** coverage rate, mentor load distribution, and the match-quality gap between priority bands. The coordinator sees distribution before she sees a single name. Putting pairs first would train her to optimise pair by pair, which is exactly the behaviour this product exists to prevent. Do not reorder it for visual convenience.

---

## Voice for all copy

Plain, warm, direct. Nigerian English over transatlantic neutral. Short sentences.

- Name people, not roles. "You've been matched with Amara", not "Your mentor has been assigned."
- Active voice. "Publish 42 strands", not "Strands will be published."
- The verb on a button is the verb in the resulting toast. Publish produces Published.
- Errors never apologise and are never vague: "That invitation expired on 3 August. We've told Ngozi you tried to join."
- Empty states are invitations, not admissions.
- No "Oops". No exclamation marks in system messages. No emoji.

## Accessibility floor

- 4.5:1 contrast under 18px, 3:1 above and for interface borders.
- Visible keyboard focus on everything. Focus trapped in modals and returned to the trigger on close.
- Every input has a real label. Placeholder is never the label.
- Colour never carries meaning alone. Every strand colour is paired with a name.
- Touch targets 44px minimum.

## Do not

Gradient buttons. Glassmorphism. Shadowed cards in a grid. Faceless-people illustrations. Emoji in system copy. Toasts for successful reads. Modals that could have been pages. Four stat tiles with percentage-change arrows. Confetti. Any hex, size or duration not listed above.

---

## Deliver

Start with the mark and a token sheet showing every colour, type style, spacing step, radius and shadow in use. Then the six components. Then the eight screens at both widths. Show empty and loading states alongside the populated ones, not as an afterthought.