# TSX output

Convert the built HTML into a single self-contained React component the user can drop into their codebase. The geometry and content are identical to the HTML; only the packaging changes.

## Shape

```tsx
// ArchDiagram.tsx — no props required, no dependencies
const ICONS = {
  hono: "data:image/svg+xml;base64,...",
  // one entry per node, copied from the built HTML's data URIs
} as const;

const T = {
  paper: "oklch(98.5% 0.004 250)",
  ink: "oklch(24% 0.02 258)",
  accent: "oklch(54% 0.2 256)",
  rule2: "oklch(83% 0.011 255)",
  // ... mirror every :root token: drop the "--color-" prefix and camelCase the rest
  // (--color-paper-2 → paper2, --color-rule-2 → rule2, --color-g1-ink → g1Ink, --color-accent-soft → accentSoft)
} as const;

export default function ArchDiagram() {
  return (
    <div style={{ overflowX: "auto", border: `1px solid ${T.rule2}`, borderRadius: 10 }}>
      <div style={{ position: "relative", width: 1000, height: 540, background: T.paper, /* grid via backgroundImage */ }}>
        {/* groups, svg edges, nodes — same coordinates as the HTML */}
      </div>
    </div>
  );
}
```

## Rules

- **Self-contained**: data-URI icons in a const, tokens in a const, inline `style` objects. No CSS files, no Tailwind assumptions, no imports beyond React. It must compile in any TSX project as-is.
- **Use the template's system font stacks** (`system-ui...`, `ui-monospace...`). The component inherits nothing from the app's font pipeline, and label widths stay close to the rendered HTML.
- **Keep the credit.** Put `// %%CREDITS%%` in the leading comment of the draft so `build.py` fills it, or copy the text from the built HTML's footer.
- Convert CSS classes to small local components or mapped style objects (`<Node cx={342} top={190} icon="tanstack" name="TanStack Start" role="frontend / ssr" dark? />`) — this keeps the file readable and makes the user's later edits easy, which is the point of asking for TSX.
- The SVG edge overlay transfers as-is (JSX-ify attribute names: `stroke-width` → `strokeWidth`, `marker-end` → `markerEnd`, `paint-order` → `paintOrder`).
- Hover states from the template (accent border on tile) become `onMouseEnter`/`Leave` state or are simply dropped — ask only if the user cares.
- Deliver it to the user's project as `<Name>Diagram.tsx`. It is code for their repository, so a logo inside it enters that repository: check with the user before committing one, because the data URIs carry the marks.
