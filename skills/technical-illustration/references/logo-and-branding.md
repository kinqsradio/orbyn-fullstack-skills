# Put a logo in a video

A logo belongs to its owner, so its rules come first. Read the brand guide if there
is one, and let it override everything here.

## Start from the supplied file

Use the logo the user supplied, in the best format available: SVG, then a transparent
PNG at least as large as its size on screen.

- Never redraw, retype or trace a logo, and never invent one. If none was supplied,
  use the name as plain text and say so.
- Never stretch, rotate, recolour, outline or add effects unless the brand guide
  allows it. Keep its aspect ratio by setting one dimension only.
- Check that transparency is real. A checkerboard or white box baked into the image
  means the file is wrong, so ask for a better one.
- Use a third party's logo only with permission from its owner or the user's
  confirmation that they hold it. Keep it out of anything implying endorsement.
- Ask which version fits a dark and a light background. Use the owner's single-colour
  version over busy art.

## Decide the job

| Use                 | How long                  | Placement                                 |
| ------------------- | ------------------------- | ----------------------------------------- |
| Corner mark         | Throughout or by section  | One corner, inside the safe area          |
| Intro sting         | 3 to 5 seconds            | Centre, then clear the frame              |
| End card            | At least 3 seconds        | Centre, with one call to action           |
| Sponsor or co-brand | Agreed with both owners   | Separated, sized as agreed                |
| Inside the artwork  | Whatever the art requires | Part of the source; keep it undistorted   |

## Place it

- Keep clear space around it. The brand guide sets this. Otherwise use the height of
  the logo's main letter or about a quarter of its height.
- Keep a corner mark to 8 to 12% of the frame width, and large enough to recognise on
  a phone.
- Keep it out of the lyric and caption zone, and out of platform buttons on vertical
  video. Hold one position; a mark that jumps between shots reads as a mistake.
- Reduce a corner mark to 70 to 90% opacity if it distracts, unless the brand guide
  forbids it. Keep full opacity for end cards.

## Animate it

Keep the reveal simple, and let it finish clean: the final held frame must show the
exact logo, sharp and complete.

- With an SVG, animate its real parts: draw on, fade or slide them into place. Change
  only timing and position, never the final shapes.
- With a PNG, use a fade, scale from 95%, or a masked wipe.
- Use the `logo` primitive for an approved text or raster reveal. It takes no
  arbitrary SVG or HTML, so a custom SVG reveal belongs in the
  [code-driven motion contract](../../orbyn-ui-design/examples/spatial-review/motion/README.md).
- Time the landing to a beat or the end of a phrase. Keep any sound short.
- Hold the finished logo for at least 1.5 seconds, so it can be read.

For a logo inside supplied art, and when the user approves OpenCV,
[still to layers](still-to-layers.md) can mask it for relighting. Keep its shape unchanged, because a glow is fine and a warp isn't.

## Check it

Render a plate with the logo hidden, then run the
[legibility check](video-scenarios.md#check-words-and-logos) with the logo's main
colour and `--min-contrast 3`. Then look at the finished video for these:

- The final frame matches the supplied logo, at the right proportions and colours.
- Edges are clean, with no dark or white halo from the alpha channel.
- It stays readable on the brightest and busiest moments, and at phone size.
- Video compression has not smeared fine detail or shifted a brand colour noticeably.
  Compare it with the source file, because colours can shift during encoding.

Report which logo file and version you used, and anything the brand guide left open.
