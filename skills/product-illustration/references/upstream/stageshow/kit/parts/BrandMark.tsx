import type { CSSProperties } from 'react'
import { useLook } from '../looks'
import './BrandMark.css'

export type BrandMarkProps = {
  /** The accessible label, and the initial shown when there is no artwork. */
  name: string
  /** A logo the consumer supplies and is allowed to use. The kit bundles none. */
  src?: string
  size?: number
  width?: number
  tile?: boolean
  className?: string
  style?: CSSProperties
}

/** The consumer's own logo, or the neutral initial tile of a fictional product.
 * On a tile the mark is inset; bare (`tile={false}`, an app header's logo) it
 * fills `size`. Artwork keeps its proportions and is never fetched by the kit. */
export function BrandMark({ name, src, size = 28, width, tile = true, className, style }: BrandMarkProps) {
  const { fidelity } = useLook()
  return (
    <span className={`ss-brand${className ? ` ${className}` : ''}`} data-tile={tile || undefined} style={{ width: width ?? size, height: size, borderRadius: Math.round(size * 0.24), ...style }} role="img" aria-label={name}>
      {src && fidelity !== 'minimal'
        ? <img src={src} alt="" draggable={false} />
        : <span className="ss-brand__initial" style={{ fontSize: Math.round(size * (size < 24 ? 0.5 : 0.42)) }}>{fidelity === 'minimal' ? '' : name.trim()[0]?.toUpperCase()}</span>}
    </span>
  )
}
