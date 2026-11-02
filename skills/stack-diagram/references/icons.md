# Icons: sources, specs and placement

`fetch_icons.py` writes one job's icons into a working folder and records each source in `manifest.json`. Read this when a logo misses, looks wrong, or needs a group label.

## Spec forms

```bash
# Offline, the default: every spec becomes a pictogram.
python3 scripts/fetch_icons.py output/my-job/icons client:generic/user api:generic/server hono~server

# The user asked for logos and the network is available.
python3 scripts/fetch_icons.py output/my-job/icons --allow-network tanstack hono~server \
  "betterauth:better-auth" "orpc=https://orpc.example/logo.webp" "cron:lucide/clock"
```

| Spec | Meaning |
| --- | --- |
| `name` | The slug equals the name |
| `name:slug` | A different slug |
| `name=URL` | One explicit https URL |
| `name:lucide/<icon>` | Lucide line icon, from lucide.dev/icons |
| `name:aws/<Name>` | AWS's own icon. Read [AWS diagrams](aws.md) |
| `name:generic/<kind>` | Bundled pictogram, never fetched |
| any of these with `~kind` | The pictogram to use if the fetch fails |

Bundled kinds: `box` (the default fallback), `branch`, `browser`, `check`, `database`, `device`, `document`, `folder`, `internet`, `link`, `server`, `terminal`, `user`. A node named after a kind uses that kind as its fallback.

A slug tries svgl, then devicon, then gilbarbara/logos. svgl must match the title exactly, so a miss falls through. svgl comes first because it carries current official marks for modern developer brands.

## When a logo misses

The run prints `FALLBACK name` and records `fallback: true` with the reason. Find the official file before accepting the pictogram:

1. Look in the project's repository: a root `logo*.svg`, then `docs/`, `assets/`, `public/`.
2. Look on its site: `/logo.svg`, `/favicon.svg`, `/images/logo.svg`.
3. Pass it as `name=URL` and fetch again.

`REFUSED name` means a limit stopped the file: not https, too large, not an image, or an SVG whose styling reaches outside itself. Removing that styling would change the logo's colours, so the file is skipped. Choose another source and leave the limit in place.

## What the fetch guarantees

Every request is https, with no credentials in the URL, a 2 MiB limit (256 MiB for AWS's package, held in memory), a total deadline that covers headers and slow drips, and redirects only to https. Private, local and reserved addresses are refused, including forms that embed one, and the connected address is checked as well as the name. A carrier's own NAT64 prefix can still hide a private IPv4 address behind a hostname. The file type comes from its bytes. SVG passes `sanitise_svg.py`, an element allowlist that drops scripts, `foreignObject`, animation, event attributes, entity declarations and every external reference. `build.py` sanitises again, so hand-placed files get the same treatment. The manifest's `sanitised` field lists what was removed; a logo with entries there deserves a look.

With `--allow-network`, the script refuses a folder Git would commit, and it stops when Git cannot confirm otherwise. `build.py` and `render_png.py` apply the same check to logo output unless the user asked for `--allow-tracked`. Never pass a logo into a tracked path, and never add one to this skill.

## Placing marks

- **White or light logo.** Use a dark tile (`tile dark`). The manifest's `white_fill` flag is a heuristic: a white fill can be an inner detail on a coloured mark, so read the SVG first.
- **Vendor sub-products** such as a vendor's database or object store usually have no distinct logo. Reuse the vendor logo and let the node name carry the difference.
- **Concepts** such as a queue, cache, cron job or webhook have no brand. Use a pictogram. Text in a tile and emoji both read as unfinished.
- **Pictograms** are not logos, so tinting one to the diagram's ink is fine.
- **Group-label icons render at 14px.** They need a square mark. A wordmark turns to mud at that size, so fetch the brand's square icon separately.
- **Group labels sit on the group's tint, not a white tile.** In the dark theme a mark with black parts vanishes. When the fetch saved `<name>_dark`, use the template's `lt`/`dk` pair. Otherwise add class `plate` to the label's `<img>` for a white backing in the dark theme only. Pictograms in group labels need `plate` too. `build.py` pairs the two automatically whenever a `<name>_dark` file exists.
- **Raster logos** (PNG, WebP, JPEG) are fine. `build.py` embeds everything as data URIs.
