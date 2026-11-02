# Gold examples

Read this to choose the example to copy. Film the closest one before you start. Gold examples are the quality bar; specimen sheets are catalogs, not compositions. `teaching/` holds bad/good pairs (`teaching.md`) for diagnosing a problem; the bad halves are never starting points. Product names in the examples are invented.

## Gold

| Need | Example | What to learn |
|---|---|---|
| Still or feature card | `static-card` | Quiet hierarchy, a hard crop, one satellite, real words only on the selected customer, its neighbors and the total |
| Dark still | `dark-bento` | One signal said once; cover art keeps it a music app |
| Animated hero, a gesture | `hero-demo` | Five beats, named targets, an annotation, a terminal coming forward |
| Choreography, no cursor | `payout-flow` | Slow overlapping arrivals, reading time, a payoff that holds |
| Content changing in place | `choreography` | Retained tracks, soft masks, dependent timing |
| AI answer | `ai-chat` | The question sent, Thinking, the answer streaming in with its height, sources last; no sparkles, no purple |
| AI with cards | `ai-cards` | A multiple-choice card answered and kept as the record, a card of options opening in the thread, booked from its own button |
| Form validation | `form-error` | An error on the field that caused it, cleared by fixing it, then the button confirms on itself |
| Drag to reorder | `reorder` | A row lifted by its grip, the others making room, dropped into place |
| Chart scrub | `chart-scrub` | A hairline and dot that follow the pointer, the headline value rolling to the day under it |
| Edit in a table | `table-edit` | A cell edited in place, then the total it feeds rolls a beat later |
| Loading to content | `loading` | A skeleton at the content's own geometry, rows resolving top to bottom, real chrome throughout |
| Dark hero | `dark-hero` | Depth from surface steps on black, one lit color, a status that changes on its own pill |
| Live collaborators | `presence` | Each person one color everywhere, names riding their cursors, work shown in the doc's own marks |
| System story | `subscriptions` | A chip flies into a row, MRR rolls, a second scene is the reset |
| Close-up | `close-up` | One control at 1.4x with its window's chrome, the row whole, a large cursor to match |
| Many of one | `many-of-one` | A grid of one thing off every edge, one tile in focus by depth, the only one with words |
| Fade crop | `fade-crop` | A window fading out at its foot, over filler, instead of running off an edge |
| Panel over product | `panel-annotation` | A settings panel over the product's margin, one leader from the setting to what it changed |
| Overlapping windows | `overlap` | A card in front of a window, its edge on the window's sidebar line |
| Stacked cards | `stacked-cards` | Two components at one width, a small gap, the lower one off the bottom |
| Opposite corners | `opposite-corners` | A bento tile: copy bottom-left, the product hung from the top-right corner |
| Tilted stack | `tilted-stack` | A loose pile of paper, small alternating angles, only the top card has words |
| Corner chip | `corner-chip` | A small chip centered on a window's corner, half outside |
| Row of windows | `window-row` | Sessions side by side at one height: focus by depth, neighbors cut by the stage, only filler cropped |
| Window and phone | `device-pair` | A dashboard and a lock screen telling one event; the phone straddles over margin, never over the figure |
| Related objects | `story` | An invoice, a plan, a connector, rolling totals |
| Calendar drag | `calendar` | A populated week, one focal event, a measured pickup |
| Free dragging | `freeform-drag` | Grab offset, a measured grid, a drop slot that snaps |
| Phone app | `phone-touch` | A card opens into its screen as one object, and the loop folds back |
| Status island | `status-island` | One black shape, its content a separate layer |
| Messages | `messages` | Composer, typing, receipts, a bubble's lifetime |
| Cursors | `cursors`, `cursor-morph`, `cursor-resize` | Five styles, element-driven kinds, resize edges and corners, no cursor at all |
| Annotations | `annotations` | Leaders, dimensions, flows and a moving target; `annotations.md` |
| Feature grid | `bento` | One hero, one window, a stat, an object, a diagram |
| Dark ruled grid | `ruled-bento` | Shared rules and technical imagery |
| Consumer grid | `staggered-bento` | Offset tiles, graphic art, physical objects |
| Image-led hero grid | `hero-grid` | Different grounds and materials composed as one picture |
| Upload | `upload` | A file dragged in from the desktop, an upload row with progress that settles as a file row |
| Share | `share` | A share popover over a document: an email becomes a chip, a role menu, a person added to the list |
| Swipe | `swipe` | A phone swipe to archive: press, swipe, a throw at the finger's speed, the gap closes |

If no gold tells your story, choose in two parts. Pick the layout from the table in `framing.md` and copy that example even though its story differs. Then borrow the motion for your beats from the example whose story is closest, and build what neither has in the same style.

## Specimen and reference sheets

Catalogs of parts and grounds, described in `kit.md` (Specimen sheets). Look up a part here; compose from a gold example.

| Need | Example | What to learn |
|---|---|---|
| Kit specimens | `chrome`, `phones`, `controls`, `parts`, `kit-extras` | Every frame and part |
| Glass | `glass` | Frosted surfaces over a color field |
| Backgrounds | `backgrounds` | One interface over twenty grounds; `backgrounds.md` |
| A product's look | `looks` | Type, shape and color working together |

## The kit

Copy `kit/` into the project and import from `kit/index.ts`. It needs React, react-dom and lucide-react (for `Icon`, which `Field` and `Chip` use); each part brings its own CSS.

- **The stage.** `Stage`: design size and scale-to-fit, `compact`, scene state, playback, the look, the cursor. The script gets an `Act`.
- **Frames.** `Window`, `Phone` with `LockScreen` and `Notification`, `Keyboard`, `Thread` with `Bubble`, `Stamp`, `Receipt`. Never draw a window, device or bubble by hand.
- **Motion.** `Collapse`, `Roll`, `Swap`, `Count`, `Connector`, `Fly`, `Follow`, `States`, `Stream`, `Popover`, `Scroll`, `Camera`, `Expand`.
- **Small parts.** `Bar`, `Text`, `Row`, `Avatar`, `Pin`, `Icon`, `Menu`, `Field`, `Segmented`, `Toggle`, `Tabs`, `Badge`, `Chip`, `BrandMark`, `Code`, `Chart`. Restyle them to the product; never reshape a kit part's geometry from outside.
- **`stageshow.css`**: tokens, looks, edge fades, chrome, phones, keycaps.
