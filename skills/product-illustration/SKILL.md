---
name: product-illustration
description: "Build faux product UI as stills or animated cursor demos: heroes, feature cards, bento grids, cursor walkthroughs. Use orbyn-ui-design for real product screens, technical-illustration for films and model-driven figures, social-preview for posters."
---

# Product illustration

Use this for miniature product UI: a believable interface, framed in its space, as one still or a short animation in which one thing happens. These are authored illustrations, not browser automation: `a.click()` draws the cursor pressing, `a.set()` changes the scene. The React kit derives from Stageshow.

The kit root is `references/upstream/stageshow/`. In the references, `kit/`, `examples/`, `teaching/` and `scripts/` mean folders there.

## The one idea

**It reads as a real product, simplified to what the viewer needs, framed with intent, and every motion has a cause.**

Five ways it fails:

- **Too much.** Real text in every row, numbers everywhere. The more detail, the more it looks generated.
- **Wireframe.** Two gray blobs and a button: built too small, or stripped of what made it recognizable.
- **Boxed.** A whole window shrunk into a card with even margins: a screenshot pasted in.
- **Flat.** Every object the same weight in the same bordered card. The eye has nowhere to land.
- **Bland.** A gray window with a cursor, whatever the brief said. The brief's look and energy are the point.

The fix: a full, structured screen in quiet grays, real words only on what the story is about, placeholder lines elsewhere, room to breathe, and a crop that puts the eye on the story. Simplify the words, not the context.

## How hard to press

Build it the way a product designer builds a launch page they will be judged on. The gold examples are the bar: if yours is the emptier, flatter or smaller one beside the closest gold, fix that first. Then picture the most exacting designer you know screenshotting the one wrong thing: a dot off its avatar, a unit on its own line, copy touching a card. If you can picture that screenshot, you have found the next fix.

## Method

1. **Plan first.** Write where it sits, the focal object, the action, the payoff and what can be left out. Choose still or animation (loop, once in view, or hover). Design at shown size: about 720 × 340 for a hero beside copy, 900 to 1100 wide for a full-width hero, 400 × 300 for a card. Any demo that can sit in a phone column ships a `compact` redesign at 358. For a grid, plan the set with [bento](references/bento.md).
2. **Set up a working copy.** Copy the kit root outside the library, or copy `kit/` into the project's React app. Run `npm install --ignore-scripts` only in that copy, so the library stays free of `node_modules` and lockfiles. `npm run dev` serves the playground on 127.0.0.1. Offline, use dependencies already on disk and report what you could not run.
3. **Choose the look.** Map the user's product tokens to the kit's ([looks](references/looks.md)), or pick a theme, palette and fidelity. Default to light, accent, standard. Give a brief with a style that style in full. Name the product: the user's own, or a fictional one.
4. **Write the story.** Three to five beats and a payoff, 10 to 16 seconds, with no cursor move you can't explain. Between a richer story and a calmer frame, choose the frame ([motion](references/motion.md)).
5. **Start from the closest gold.** Find it in [gold examples](references/gold-examples.md), film it, and copy its folder to `examples/<yours>/`, where `?capture=<yours>` films it. Keep its stage size, crop, spacing, beats and kit parts. Read [craft](references/craft.md) in full. Replace the look and content; a copy that only changes the name is unfinished. Then frame it ([framing](references/framing.md)) and film one still beside the gold's at both widths. If yours is emptier, flatter or more boxed, fix the frame before any motion.
6. **Build the screen.** Spend 3 to 7 real strings. Build with kit tokens, `Bar`, `Text` and `Row`. Mark what the cursor touches with `data-target` and `data-cursor`; measure with `rect()`, never hard-code ([kit](references/kit.md)).
7. **Choreograph.** Keep what appears mounted and toggle it so exits animate. Animate the relationship: a new row carries the rows below it. Beats overlap, the payoff holds, and the loop ends where it began or resets with a visible cause.
8. **Rehearse for real.** Set `poster` first: the beat that tells the story alone, with the result on screen. Film the loop, not just a still: `node scripts/film.mjs "<url>/?capture=<yours>" --select '#example' --gate` at shown width, again with `--width 390`, and with `--states`. Read every frame, fix the largest visible fault first (framing, hierarchy, motion, polish) and re-film. `rehearsal passed` is necessary, not sufficient. Finish with [rehearse](references/rehearse.md), [verify](references/verify.md) and `REHEARSAL.md` beside the component, naming the gold, what changed and what you did not check.

Worked failure: a brief asks for a hero showing invoice approval. The first build is a complete window, 480 wide, centered on a tinted plate, with real names in all twelve rows. The gate passes, but beside `static-card` it reads as a screenshot. Largest fault first: remove the plate, run the window off the bottom edge at 720 wide, keep real words on the selected row and its total, and turn the other rows into bars. Then the approval moves the total, because that is the payoff.

## Check these before handing over

Each comes back every round:

- Content that swaps instead of moving.
- Gray bars where the eye lands; filler belongs at the edges.
- A plate behind the window, or a window floating with air on four sides.
- Empty bands, cut controls and cut shadows.
- Stock AI and made-up logos: sparkles, purple, a letter in a colored square.
- Busy rows and uneven insets.
- Long holds and a reset with no cause.
- A selection that isn't under the I-beam.
- A status bar or home indicator drawn by hand; the `Phone` draws both.
- A centered amount centered with its sign.

## Boundaries

- Show the user's own product or a fictional one. A request to recreate a real company's app gets a generic product with the same interaction; never that company's name, logo, look or UI ([interaction lessons](references/interaction-lessons.md)).
- Logos come from the user ([logos](references/logos.md)). The kit bundles none.
- Web illustrations use React as their host runtime. A video that uses the kit follows the [code-only rule](../technical-illustration/references/code-only.md).
- A fresh-eye review is a [separate reader](references/review.md) when the host offers one. Report your own pass as a self-check.

## Read when needed

- For the example to copy: [gold examples](references/gold-examples.md).
- For a part's props: [kit](references/kit.md).
- For the still frame: [craft](references/craft.md) and [framing](references/framing.md).
- For story, loops and cursors: [motion](references/motion.md); for overlapping changes: [choreography](references/choreography.md).
- For a grid: [bento](references/bento.md); for grounds: [backgrounds](references/backgrounds.md).
- For leaders and dimensions: [annotations](references/annotations.md).
- For the user's product tokens: [looks](references/looks.md).
- For a logo: [logos](references/logos.md).
- For a familiar product category: [interaction lessons](references/interaction-lessons.md).
- For filming and film lines: [rehearse](references/rehearse.md); for the last checklist: [verify](references/verify.md).
- For a fresh-eye brief: [review](references/review.md).
- For diagnosing a fault against bad/good pairs: [teaching](references/teaching.md).
