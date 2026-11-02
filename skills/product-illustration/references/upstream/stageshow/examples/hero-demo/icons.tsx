import { Check, Copy, Eye, List, Pause, Settings, Trash2, X } from 'lucide-react'

// The toolbar's icons, one family at one weight.
const ICONS = { 'list-sparkle': List, pause: Pause, eye: Eye, copy: Copy, check: Check, trash: Trash2, gear: Settings, x: X } as const

export function Icon({ name, size = 18 }: { name: keyof typeof ICONS; size?: number }) {
  const Glyph = ICONS[name]
  return <Glyph size={size} strokeWidth={1.5} absoluteStrokeWidth aria-hidden />
}
