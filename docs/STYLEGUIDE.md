# UI Style Guide

How the Repair Café app presents information. Every page follows these rules; the
shared components in `frontend/src/components/ui/` implement them, so pages use those
instead of styling things themselves. Base: Vuetify 4 (Material Design 3) defaults.

Enforced by lint (`frontend/eslint.config.js`): outside `components/ui/`, no raw
`<v-chip>` (except closable filter chips) and no palette colors (`teal`, `grey-*`, …)
in `color` / `dot-color` / `bg-color`. Admins see every building block at `/styleguide`.

## Principles

1. **Built for the workbench.** Tablets and the shared workshop PC, used with dirty
   hands and in a hurry: large touch targets (≥ 48 px), the next step always visible,
   few taps for the main flow (scan → log work → close).
2. **One meaning per color.** A color either says *which status a repair has* or
   *how an action went* — never both.
3. **Same thing, same look.** A status, a person, a date or a repair number looks the
   same on every page. If two pages show it differently, one of them is wrong.
4. **Structure through layout, not decoration.** Cards, spacing and headings group
   information; color and chips are reserved for things that need to stand out.
5. **Calm by default.** Most text is plain. Emphasis (color, chips, bold) is rare, so it
   still means something.

## Colors

| Role | Token | Used for | Never for |
|---|---|---|---|
| Brand / action | `primary` | app bar, main buttons, links, selected navigation | statuses, messages |
| Repair status | `status-open`, `status-in-progress`, `status-repaired`, `status-not-repaired` | status chips, repair number avatars, status buttons | anything else |
| Feedback | `success`, `info`, `warning`, `error` | toasts, alerts, form validation, VDE test result, destructive actions (`error`) | statuses, decoration |
| Neutral | default surface / `medium-emphasis` text | everything else | — |

Status hues stay as people know them (amber = open, blue = in progress, green =
repaired, red = not repaired), but as their own theme colors, defined once in
`plugins/vuetify.ts`. No palette colors (`teal`, `grey-darken-1`, `blue-lighten-1`, …)
in templates.

## Chips

Chips are only for **short values from a fixed set** that the user scans for.

| Value | Component | Look |
|---|---|---|
| Repair status | `StatusChip` | tonal, status color, status icon, square corners (`label`) |
| Category (repair type) | `TagChip` | tonal, neutral, `mdi-tag-outline` |
| Count (tabs, section headers) | `CountBadge` | x-small, neutral |
| Active / inactive (users, settings) | `StatusChip` (generic variant) | tonal, success / neutral |
| Active filter (e.g. customer in the repair list) | `v-chip closable` | tonal, removable |

**Not chips:** people, dates, durations, free text, IDs, anything clickable that is
really a button.

## People

People are shown with `PersonLabel`: role icon + full name, plain text.

| Role | Icon | Example |
|---|---|---|
| Customer (Kunde) | `mdi-account` | 👤 Erika Muster |
| Repairer (Reparateur, assignee) | `mdi-account-wrench` | 🔧 Hans Müller |
| Author of an entry, tester (Prüfer) | no icon, after the date | 03.11.2026, 16:09 · Hans Müller |

- Name format everywhere: **Vorname Nachname** (helper `personName()`); fallback is
  the username, then "–". Nobody builds names by hand.
- Contact details (phone, e-mail) only where you'd act on them (repair detail,
  customers), as tap-to-call / tap-to-mail links.
- "Nobody assigned" is shown as text in `medium-emphasis`: *Niemand zugewiesen*.

## Repair identity

- Repair number: `#23` in text; in cards and headers an avatar with the number in the
  repair's status color.
- Title of a repair is the device (`geraet_art`); customer and category are secondary.

## Dates and numbers

- Always German format, independent of the browser language: `03.11.2026`,
  `03.11.2026, 16:09`. Helpers in `utils/date.ts`.
- Durations: `45 Min.`

## Typography

| Element | Class |
|---|---|
| Page title | `text-headline-small` (in `PageHeader`) |
| Section title | `text-title-large`, with a leading icon |
| Card title | `text-title-large` |
| Field label above a value | `text-title-small text-medium-emphasis` |
| Body text | `text-body-medium` (`text-body-large` for the main text of a card) |
| Meta (dates, authors) | `text-body-small text-medium-emphasis` |

## Layout

- Pages: `<v-container fluid class="page-container">` (max width 1400 px, centered;
  defined in `src/styles/main.css`), `PageHeader` (title, optional subtitle and actions),
  content in cards. Only the lock screen (wall display) is wider.
- Action bars and step content line up with the page content (no extra side padding).
- Spacing on the 4 px grid; between cards `mb-4`, inside groups `ga-2`.
- Small screens: one column, tabs instead of side-by-side sections, the main action in
  a bottom bar or `v-fab`; dialogs fullscreen (`ResponsiveDialog`).
- Loading: skeletons in the shape of the content; empty: `v-empty-state` with icon and
  one sentence.

## Buttons and actions

| Action | Look |
|---|---|
| The main action of a view (one per view) | `variant="flat"`, `size="large"` on touch views |
| Status change | color of the target status, status icon |
| Secondary actions | `variant="tonal"` or `text` |
| Destructive (delete, deactivate) | `color="error"`, `variant="text"`, always with confirmation |
| Icon-only buttons | always with `aria-label` |

Always set `variant` explicitly: Vuetify picks different defaults by context (e.g.
`text` inside `v-card-actions`), so the same action would look different on every page.

## Wording

German throughout; no English UI text (today e.g. the QR scanner still says "Scan QR
Code"). "du" towards helpers, "Sie" in everything the customer reads or signs
(disclaimer, cancellation). Short labels, verb + object: "Reparatur starten",
"Logeintrag speichern".
