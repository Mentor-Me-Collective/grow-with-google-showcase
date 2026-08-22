# UI Design System

Written spec for the app's visual and interaction design, owned by Sehr Abrar (UX/UI Lead).

The design was built directly in code rather than mocked in a separate design tool, so this document is the design file: it records the tokens, rules, and rationale that `frontend/src/index.css` and `frontend/src/App.css` implement. Every value below is the shipped value, not a proposal. The research that drove these decisions is in [user-research.md](./user-research.md).

---

## 1. Typography

| Property | Value |
|---|---|
| Typeface | Plus Jakarta Sans (Google Fonts, weights 400, 500, 600, 700, 800) |
| Fallback stack | `system-ui`, `-apple-system`, `Segoe UI`, `sans-serif` |
| Headings (`h1`, `h2`, `h3`) | Weight 600, zero margin (spacing is owned by layout, not headings) |
| Rendering | `-webkit-font-smoothing: antialiased` |

One typeface across the whole app. Weight and size carry hierarchy, so there is no secondary display or monospace face to keep consistent.

---

## 2. Color tokens

All color is referenced through CSS custom properties, never hardcoded in components. This is what makes four themes possible without touching component code.

### Structural tokens

| Token | Light | Dark | Sepia | Role |
|---|---|---|---|---|
| `--page` | `#f9f9f7` | `#0d0d0d` | `#ece0c4` | Page background |
| `--surface` | `#fcfcfb` | `#1a1a19` | `#f4ecd8` | Card and panel background |
| `--text-primary` | `#0b0b0b` | `#ffffff` | `#3b2f26` | Body and heading text |
| `--text-secondary` | `#52514e` | `#c3c2b7` | `#6b5c4d` | Supporting text |
| `--text-muted` | `#898781` | `#898781` | `#8a7a68` | Labels, captions, de-emphasized text |
| `--gridline` | `#e1e0d9` | `#2c2c2a` | `#e3d8bf` | Chart gridlines, dividers |
| `--baseline` | `#c3c2b7` | `#383835` | `#cdbd9d` | Baseline comparison marks in charts |
| `--border` | `rgba(11,11,11,.1)` | `rgba(255,255,255,.1)` | `rgba(59,47,38,.15)` | Card and control borders |

Note that `--page` is never pure white and `--text-primary` is never pure black in light mode. Both are warmed slightly to reduce glare, which is the same motivation behind offering the sepia theme.

### Categorical series palette

Eight slots, used for per-appliance identity in charts and breakdowns.

| Token | Light / Sepia | Dark |
|---|---|---|
| `--series-blue` | `#2a78d6` | `#3987e5` |
| `--series-green` | `#008300` | `#008300` |
| `--series-magenta` | `#e87ba4` | `#d55181` |
| `--series-yellow` | `#eda100` | `#c98500` |
| `--series-aqua` | `#1baf7a` | `#199e70` |
| `--series-orange` | `#eb6834` | `#d95926` |
| `--series-violet` | `#4a3aa7` | `#9085e9` |
| `--series-red` | `#e34948` | `#e66767` |

Sepia deliberately reuses the light series values; only its surfaces and text shift. Dark mode retunes each hue for legibility against a near-black background rather than reusing the light values.

### Status palette

| Token | Value | Meaning |
|---|---|---|
| `--status-good` | `#0ca30c` | Better than baseline |
| `--status-warning` | `#fab219` | Room to improve |
| `--status-serious` | `#ec835a` | Elevated usage |
| `--status-critical` | `#d03b3b` | High usage |

Status colors are defined once and **not** overridden per theme, so a "good" green means the same thing in every theme. `--brand-purple` (`#863bff`) is likewise theme-constant.

---

## 3. Appliance color assignment

Implemented in [`frontend/src/lib/applianceColors.ts`](../frontend/src/lib/applianceColors.ts), where the reasoning is also recorded in a header comment.

Appliance colors are **hardcoded, never generated**. A categorical palette intended to stay distinguishable for color-vision-deficient users caps out at 8 hues, but the app ships 11 built-in appliances. Three pairs therefore share a hue by necessity:

- Microwave / Air Conditioner (blue)
- Dishwasher / Washing Machine (magenta)
- LED Lights / Television (yellow)

Each pair is spread apart in appliance ordering so the two rarely appear as adjacent segments, and identity is made exact by the hover and focus highlight plus the legend. Color is a fast lookup, not the only channel carrying meaning.

User-added custom appliances fall outside the fixed set and all share one neutral (`--text-secondary`), which visually distinguishes "your own entry" from the benchmarked built-ins.

---

## 4. Score status thresholds

From [`frontend/src/lib/scoreStatus.ts`](../frontend/src/lib/scoreStatus.ts). The Personalized Energy Score runs 1 to 100 and maps to three states:

| Score | Color | Label |
|---|---|---|
| 80 and above | `--status-good` | "Better than baseline" |
| 50 to 79 | `--status-warning` | "Room to improve" |
| Below 50 | `--status-critical` | "High usage" |

Every state carries a **text label alongside the color**, which comes straight from the research finding that users distrust a bare number and won't infer meaning from a hue alone.

---

## 5. Shape and elevation

| Token | Value | Applied to |
|---|---|---|
| `--radius-card` | `16px` | Cards, panels, tiles |
| `--radius-control` | `10px` | Buttons, inputs, toggles |
| `--shadow-card` | Two-layer: `0 1px 2px` contact shadow plus `0 4px 16px` ambient | Cards |

Shadow opacity is retuned per theme (roughly 4% in light, 20 to 30% in dark, 6% in sepia) because a shadow tuned for a light background disappears against a dark one.

Two radii only. Anything card-shaped gets 16px, anything interactive gets 10px.

---

## 6. Theming

Four user-selectable preferences, implemented in [`frontend/src/lib/theme.ts`](../frontend/src/lib/theme.ts):

| Preference | Mechanism |
|---|---|
| `system` | No `data-theme` attribute, so `@media (prefers-color-scheme: dark)` decides |
| `light` | `data-theme="light"`, which also wins against the OS dark preference |
| `dark` | `data-theme="dark"` |
| `sepia` | `data-theme="sepia"` |

The choice persists in `localStorage`. Selecting `system` **removes** the stored key rather than storing the literal string "system", so the app follows later OS changes instead of freezing whatever the OS happened to prefer at selection time.

Sepia is reachable only by explicit selection, since no OS-level signal for "warm, low-glare reading" exists. The dark theme is applied through both a `prefers-color-scheme` block and an explicit `data-theme="dark"` selector so it works whether it was chosen or inherited.

---

## 7. Text sizing

Four steps, implemented in [`frontend/src/lib/textSize.ts`](../frontend/src/lib/textSize.ts) and driven by a single `--a11y-zoom` multiplier set on the root element:

| Preference | `--a11y-zoom` |
|---|---|
| `small` | 0.95 |
| `default` | 1.08 |
| `large` | 1.25 |
| `x-large` | 1.40 |

The default is 1.08 rather than 1.0 on purpose: the research found low effort tolerance and a mix of ages among renters, so the baseline is already slightly larger than a typical web default. Because one multiplier feeds every type scale, sizing stays proportional at every step instead of breaking layout at the extremes. Like theme, `default` clears the stored key rather than persisting a no-op value.

---

## 8. Responsive behavior

Breakpoints, all `max-width` and mobile-last: **1130px**, **1120px**, **1080px**, **860px**, **720px**.

The cluster in the 1080 to 1130 range handles the sticky-column layout collapsing as the viewport narrows; 860px moves multi-column card grids to stacked; 720px is the phone layout.

---

## 9. Accessibility

Built into components rather than retrofitted:

- **ARIA attributes across 29 lines and 7 explicit `role` assignments**, concentrated in `TopBar` (navigation state), `UsageSimulator` (slider labelling), and the theme and accessibility controls. Roles in use: `dialog` for the accessibility panel, paired `radiogroup`/`radio` for the theme and text-size pickers, plus `group` and `img`.
- **`:focus-visible` styling** on interactive elements, so keyboard focus is visible without drawing a ring for mouse users.
- **Read-aloud** ([`lib/readAloud.ts`](../frontend/src/lib/readAloud.ts)) via the browser `SpeechSynthesis` API, feature-detected and degrading silently where unsupported, cancelling any in-progress utterance before starting a new one.
- **Text-size and theme controls** surfaced in a dedicated accessibility panel rather than buried in settings.
- **Sepia theme** as a low-glare reading option.
- **Print stylesheet** plus a dedicated `PrintableReport` component, so a tenant can take a physical copy of their score and tips.
- **Color is never the sole channel.** Status carries a text label, chart segments carry a legend and hover identity.

---

## 10. Known gaps

Honest list, for whoever picks this up next:

- **No `prefers-reduced-motion` handling.** Transitions run regardless of the OS setting. This is the clearest accessibility gap and the cheapest to close.
- **No recorded contrast audit.** Colors were chosen with contrast in mind and surfaces are deliberately off-white/off-black, but no WCAG AA/AAA ratio measurements are documented. Worth running a checker across all four themes and recording the numbers here.
- **Series palette collisions.** Three appliance pairs share a hue (see section 3). Mitigated, not eliminated. An icon or pattern channel per appliance would remove the ambiguity entirely.
- **No visually-hidden utility class.** Some context that is currently visual-only could be exposed to screen readers with a standard `sr-only` helper.
- **Breakpoints are slightly redundant.** Three separate values between 1080px and 1130px could likely collapse into one without visible change.
