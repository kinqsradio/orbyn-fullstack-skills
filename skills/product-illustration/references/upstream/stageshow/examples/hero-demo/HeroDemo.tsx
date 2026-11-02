import { Bar, Stage, Text, Window, between, box, contains, inset, type Act, type Point, type Rect, States } from '../../kit'
import { Icon } from './icons'
import './hero.css'

// A dev tool's hero: annotate a dashboard three ways, copy the feedback,
// paste it into a terminal agent.

type Tone = 'blue' | 'green' | 'orange'
type Marker = { at: Point; show: boolean }

type S = {
  toolbar: boolean
  highlight: boolean
  popup: { show: boolean; header: string; at: Point; tone: Tone }
  typed: string
  drag: Rect | null
  /** The marquee shows while the drag runs, and fades on release */
  dragging: boolean
  area: { r: Rect; show: boolean }
  picked: string[]
  selection: number
  selecting: boolean
  m3: Marker
  m4: Marker
  m5: Marker
  copied: boolean
  terminal: boolean
  pasted: string
}

const hidden = (m: Marker): Marker => ({ ...m, show: false })

const initial: S = {
  toolbar: false,
  highlight: false,
  popup: { show: false, header: '', at: { x: 0, y: 0 }, tone: 'blue' },
  typed: '',
  drag: null,
  dragging: false,
  area: { r: { x: 0, y: 0, width: 0, height: 0 }, show: false },
  picked: [],
  selection: 0,
  selecting: false,
  m3: { at: { x: 0, y: 0 }, show: false },
  m4: { at: { x: 0, y: 0 }, show: false },
  m5: { at: { x: 0, y: 0 }, show: false },
  copied: false,
  terminal: false,
  pasted: '',
}

const TITLE = "Maya's Dashboard"
const OUTPUT = `## Page feedback

Export button: primary style
Sidebar icons: hover states
Dashboard title: more prominence`

const REST = { wide: { x: 432, y: 212 }, compact: { x: 280, y: 200 } }
const POSTER: S = { ...initial, toolbar: true, copied: true, terminal: true, pasted: OUTPUT }

async function annotate(a: Act<S>, header: string, tone: Tone, at: Point, text: string) {
  const width = a.layout === 'compact' ? 358 : 720
  const edge = a.layout === 'compact' ? 111 : 116
  const placed = { x: Math.max(edge, Math.min(width - edge, at.x)), y: at.y }
  await a.set((s) => ({ popup: { ...s.popup, show: true, header, at: placed, tone }, typed: '' }))
  await a.wait(300)
  await a.type('typed', text)
  await a.wait(300)
  const add = a.rect('add')
  await a.click({ x: add.x + add.width * 0.82, y: add.y + add.height * 0.74 })
  await a.set((s) => ({ popup: { ...s.popup, show: false } }))
  await a.wait(200)
}

async function script(a: Act<S>) {
  await a.wait(600)

  // Open the toolbar
  await a.move('toolbar')
  await a.wait(300)
  await a.click()
  await a.set({ toolbar: true })
  await a.wait(400)
  await a.wait(200)

  // 1. Click an element
  await a.move('export')
  await a.set({ highlight: true })
  await a.wait(400)
  await a.click()
  await a.set({ highlight: false })
  await a.wait(100)
  const btn = a.rect('export')
  await annotate(a, 'button.export-btn', 'blue', { x: btn.x + btn.width / 2 - 80, y: btn.y + btn.height + 10 }, 'Change to primary style')
  await a.set({ m3: { at: a.center('export'), show: true } })
  await a.wait(600)

  // 2. Drag over an area
  const icons = a.rect('icons')
  const from = { x: icons.x + icons.width + 2, y: icons.y + icons.height + 2 }
  const to = { x: icons.x - 2, y: icons.y - 2 }
  await a.move(from)
  await a.wait(150)
  await a.drag(to, (at) => {
    const drag = between(from, at)
    const picked = ['icon-0', 'icon-1', 'icon-2'].filter((n) => contains(drag, a.rect(n)))
    a.put({ drag, picked, dragging: true })
  })
  await a.wait(200)
  await a.set({ dragging: false, picked: [], area: { r: between(from, to), show: true } })
  await annotate(a, 'Sidebar icons', 'green', { x: to.x + 110, y: (from.y + to.y) / 2 - 40 }, 'Add hover states')
  await a.set({ m4: { at: { x: from.x, y: to.y }, show: true } })
  await a.wait(400)

  // 3. Select text
  const title = a.rect('title')
  const y = title.y + title.height / 2
  await a.move({ x: title.x, y })
  await a.wait(150)
  await a.set({ selecting: true })
  await a.drag({ x: title.x + title.width, y }, (at) => a.put({ selection: a.caret('title', at) }))
  await a.wait(200)
  await annotate(a, `"${TITLE}"`, 'orange', { x: Math.max(100, title.x + title.width / 2), y: title.y + title.height + 7 }, 'Make this more prominent')
  await a.set({ selecting: false, m5: { at: { x: title.x + title.width + 2, y }, show: true } })
  await a.wait(400)

  // Copy, then paste into the agent
  await a.move('copy')
  await a.wait(400)
  await a.click()
  await a.set({ copied: true })
  await a.wait(400)
  await a.set({ terminal: true })
  await a.wait(600)
  await a.click('terminal-input')
  await a.key('cmd+v')
  await a.set({ pasted: OUTPUT })
  await a.move('rest')
  await a.wait(2000)

  // Put everything back, so the loop has no seam
  await a.set((s) => ({ ...initial, m3: hidden(s.m3), m4: hidden(s.m4), m5: hidden(s.m5), area: { ...s.area, show: false }, pasted: s.pasted, popup: s.popup }))
  await a.move('rest')
  await a.wait(400)
  await a.set({ ...initial })
}

export function HeroDemo() {
  return (
    <Stage width={720} height={340} compact={{ below: 600, width: 358, height: 300 }} initial={initial} poster={POSTER} script={script} cursor={{ at: REST }} className="hd">
      {(s, rect, layout) => (
        <>
          <Window url="localhost:3000" className="hd-browser" data-cursor={s.toolbar ? 'crosshair' : 'pointer'} receded={s.terminal}>
            <div className="hd-content">
              <aside className="hd-sidebar">
                <Bar className="hd-sidebar-logo" w={20} h={20} r={5} tone={4} />
                <div className="hd-sidebar-icons" data-target="icons">
                  {[0, 1, 2].map((i) => (
                    <Bar
                      key={i}
                      data-target={`icon-${i}`}
                      className="hd-sidebar-icon"
                      w={16}
                      h={16}
                      r={4}
                      tone={i === 1 ? 5 : 3}
                      data-selected={s.picked.includes(`icon-${i}`)}
                    />
                  ))}
                </div>
                <div className="hd-sidebar-bottom">
                  <Bar w={16} h={16} r={8} tone={3} />
                </div>
              </aside>

              <main className="hd-main">
                <div className="hd-header">
                  <div className="hd-header-left">
                    <span className="hd-logo" />
                    <span className="hd-title" data-target="title" data-cursor="ibeam">
                      <span className="hd-selection" data-show={s.selecting || undefined}>{TITLE.slice(0, s.selection)}</span>
                      {TITLE.slice(s.selection)}
                    </span>
                  </div>
                  <Bar data-target="export" w={55} h={26} r={5} tone={3} />
                </div>

                <div className="hd-metrics">
                  {[
                    [45, 50],
                    [55, 65],
                    [38, 40],
                  ].map(([label, value], i) => (
                    <div key={i} className="hd-card" data-target={`metric-${i}`}>
                      <Bar w={label} h={5} tone={3} style={{ marginBottom: 8 }} />
                      <Bar w={value} h={18} r={3} tone={4} />
                    </div>
                  ))}
                </div>

                <div className="hd-table" data-crop>
                  <div className="hd-row head">
                    <Bar w={60} tone={4} />
                    <Bar w={45} tone={4} />
                    <Bar w={40} tone={4} />
                  </div>
                  {/* Two real rows, one placeholder: a table, not a wireframe */}
                  {[
                    ['api-gateway', 'main', 48],
                    ['web', 'release-1.4', 42],
                    [62, 38, 48],
                  ].map(([a, b, pill], i) => (
                    <div key={i} className="hd-row" data-target={i === 0 ? 'row-0' : undefined}>
                      {typeof a === 'string' ? <Text className="hd-cell">{a}</Text> : <Bar w={a} h={7} tone={2} />}
                      {typeof b === 'string' ? <Text className="hd-cell hd-cell--faint">{b}</Text> : <Bar w={b} h={7} tone={2} />}
                      <Bar w={pill as number} h={18} r={9} tone={1} />
                    </div>
                  ))}
                </div>

                <Toolbar open={s.toolbar} copied={s.copied} />
              </main>
            </div>
          </Window>

          {/* Overlays, positioned from measured targets */}
          <div className="hd-highlight" data-show={s.highlight} style={box(inset(rect('export'), 4))} />
          <div className="hd-dragbox" data-show={s.dragging || undefined} style={s.drag ? box(s.drag) : undefined} />
          <div className="hd-area" data-show={s.area.show} style={box(s.area.r)} />

          <div className="hd-marker" data-show style={{ left: rect('metric-0').x + 28, top: rect('metric-0').y + 14 }}>
            1
          </div>
          <div className="hd-marker" data-show style={{ left: rect('row-0').x + 140, top: rect('row-0').y + 10 }}>
            2
          </div>
          <div className="hd-marker" data-show={s.m3.show} style={{ left: s.m3.at.x, top: s.m3.at.y }}>
            3
          </div>
          <div className="hd-marker" data-tone="green" data-show={s.m4.show} style={{ left: s.m4.at.x, top: s.m4.at.y }}>
            4
          </div>
          <div className="hd-marker" data-tone="orange" data-show={s.m5.show} style={{ left: s.m5.at.x, top: s.m5.at.y }}>
            5
          </div>

          <div className="hd-popup" data-show={s.popup.show} data-tone={s.popup.tone} style={{ left: s.popup.at.x, top: s.popup.at.y }}>
            <div className="hd-popup-header">{s.popup.header}</div>
            <div className="hd-popup-input" data-cursor="ibeam">
              {s.typed}
              <span className="hd-caret" style={{ opacity: 0.4 }}>|</span>
            </div>
            <div className="hd-popup-actions">
              <div className="hd-popup-btn">Cancel</div>
              <div className="hd-popup-btn submit" data-target="add" data-cursor="hand">Add</div>
            </div>
          </div>

          <Window title="Maya's Project" className="hd-terminal" data-show={s.terminal}>
            {/* A paste arrives as one operation after its keystroke. */}
            <div className="hd-terminal-body" data-target="terminal-input" data-cursor="ibeam" data-snap>
              <div className="hd-terminal-welcome">
                <Welcome />
              </div>
              {s.pasted}
              <span style={{ opacity: 0.4 }}>█</span>
            </div>
          </Window>
          <span data-target="rest" style={{ position: 'absolute', ...{ left: REST[layout].x, top: REST[layout].y } }} />
        </>
      )}
    </Stage>
  )
}

function Toolbar({ open, copied }: { open: boolean; copied: boolean }) {
  return (
    <div className="hd-toolbar" data-target="toolbar" data-cursor="hand" data-open={open}>
      <div className="hd-toolbar-icon">
        <Icon name="list-sparkle" size={20} />
      </div>
      <div className="hd-toolbar-buttons">
        <div className="hd-toolbar-btn">
          <Icon name="pause" />
        </div>
        <div className="hd-toolbar-btn">
          <Icon name="eye" />
        </div>
        <div className="hd-toolbar-btn" data-target="copy" data-cursor="hand" data-active={copied}>
          <States value={copied ? 'check' : 'copy'} states={{ copy: <Icon name="copy" />, check: <Icon name="check" /> }} />
        </div>
        <div className="hd-toolbar-btn">
          <Icon name="trash" />
        </div>
        <div className="hd-toolbar-btn">
          <Icon name="gear" />
        </div>
        <div className="hd-toolbar-divider" />
        <div className="hd-toolbar-btn">
          <Icon name="x" />
        </div>
      </div>
    </div>
  )
}

// The welcome box of Relay, an invented command-line tool.
function Welcome() {
  const mono = 'ui-monospace, monospace'
  return (
    <svg viewBox="0 0 240 76" fill="none" style={{ width: '100%', height: 'auto', display: 'block' }}>
      <rect x="4" y="4" width="148" height="68" rx="3" stroke="#6b7280" strokeWidth="1.5" fill="none" />
      <text x="160" y="16" fill="rgba(0,0,0,0.7)" fontSize="9" fontFamily={mono} fontWeight="500">
        Relay
      </text>
      <text x="160" y="26" fill="rgba(0,0,0,0.4)" fontSize="7" fontFamily={mono}>
        v1.4.0
      </text>
      <text x="78" y="20" fill="rgba(0,0,0,0.6)" fontSize="8" fontFamily={mono} textAnchor="middle">
        Welcome back Maya!
      </text>
      <path d="M66 32 78 41 66 50" stroke="#374151" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M81 52H94" stroke="#374151" strokeWidth="3" strokeLinecap="round" />
      <text x="78" y="64" fill="rgba(0,0,0,0.4)" fontSize="7" fontFamily={mono} textAnchor="middle">
        ~/code/dashboard
      </text>
    </svg>
  )
}
