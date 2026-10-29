# Colour role gallery

This original, self-contained HTML example uses the
[reference catalogue](../../assets/reference-palettes.json) and
[semantic-colour method](../../references/colour-palettes.md). It does not copy
the reference screenshots or update any consuming project token.

From the outer library, choose a new ignored output with an existing parent:

```sh
python3 skills/orbyn-ui-design/scripts/build_colour_gallery.py \
  --out output/colour-gallery
```

Open the resulting `index.html`. No package installation, server, network or
provider is required. The builder refuses existing output and writes a receipt
identifying source/output hashes. A byte-complete build does not establish a
rendered, usable or accessibility-compliant interface.

Try these cases:

1. Select each of the seven palettes by keyboard or pointer. Both light and dark
   proposals update locally, and the selected button keeps keyboard focus.
2. Expand semantic roles/origins and computed role-pair checks. Added white/dark
   neutrals and status colours are explicitly separate from source swatches.
3. Inspect all raw labels: blue/ice position 3 remains unknown. No sampled or
   guessed value appears in its place.
4. Tab through the preview, hover Save, submit a normal title, then empty the
   title and submit. Success is explicitly simulated; errors include text and
   focus returns to the input. The disabled example performs no action.
5. Use foreground #81737A on #FFFFFF: the display rounds to 4.50:1 but the normal
   text result stays below target. Change alpha or use identical colours to see
   how the composited pair changes; unsupported CSS stays unverified.
6. Inspect at narrow widths and with the role/check details open. Only the data
   table may scroll horizontally; surrounding content and actions must reflow.

The pair-lab sample is 16px text; its applicable text target stays 4.5:1 even if
its 3:1 large-text numeric comparison passes. A gradient/background image cannot
be qualified from these two solid input values. Focus tests, non-colour status
cues, composition and target-native behavior are separate from the calculator.
The gallery uses no storage or backend; changing collection/reloading resets the
simulated form. Existing project brands and settings remain untouched.
