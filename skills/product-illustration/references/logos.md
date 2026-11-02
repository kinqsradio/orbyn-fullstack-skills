# Logos

The kit bundles no third-party artwork. A scene uses the user's own product with the logo they supply, or a fictional product with the neutral initial tile. A real company's logo or name never appears because a scene would look more convincing with it.

```tsx
import { BrandMark } from './kit'

<BrandMark name="Your product" src="/assets/product.svg" size={28} />
<BrandMark name="Your product" src="/assets/product.svg" size={20} tile={false} />
<BrandMark name="Inkwell" size={28} />
```

`src` is a logo the user supplies and may use. Treat it as the project's asset: keep it in the project, under its terms, and never fetch it from an icon service at runtime. `name` is the accessible label, and its first letter fills the tile when there is no `src`. `size` is the footprint's height; `width` overrides the footprint when a product row has a fixed track. The artwork is always `object-fit: contain`, never stretched to fill a square. Minimal fidelity hides the artwork along with the other content.

Pass a dark variant yourself when the Stage is dark; the kit does not choose artwork. Keep a logo's own colors and proportions, even in a monochrome UI.

An initial in a brand-colored tile beside a real company's name is an invented logo, and film flags `invented mark`. Use the supplied artwork, or a fictional name with the neutral tile.

A row of integrations uses invented names with neutral tiles unless the user supplies logos they are allowed to show. It explains a relationship; it does not fill spare space with logos. Keep equal row tracks and align the marks by eye: their different silhouettes are no excuse for ragged labels or uneven gaps.

Inspect the rendered artwork, not just its image box. Tall marks need real air above and below; wide marks must show in full. Give the image a definite box inside a centered flex layout: percentage image dimensions in an intrinsic grid track can grow unexpectedly and leave uneven insets. Check the real light and dark backgrounds, not just their theme attributes.
