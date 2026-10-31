# Product-owned assistant chat — original teaching fixture

An independently authored provider-free chat shell connects the
[assistant-chat method](../../references/assistant-chat.md) to executable local
examples. It is not assistant-ui, a compatible runtime adapter or a replacement
for the consuming product's components. No package installation or network call
is required. Upstream methods are reviewed inspiration; no source/theme copied.

Serve this folder with an already available static server and open its index:

```sh
python3 -m http.server 58430 --bind 127.0.0.1 --directory skills/orbyn-ui-design/examples/assistant-chat
node --test skills/orbyn-ui-design/examples/assistant-chat/chat.test.mjs
```

Choose an available loopback port if occupied; record the actual URL and retain
the server according to the library's artifact lifecycle. Files and server
availability alone do not establish that a browser interaction was inspected.

## Ownership and states to try

- `chat.mjs` owns a bounded scoped draft, admitted send snapshot, simulated
  outcomes, attachment metadata and delivery generation. It does not authenticate
  anyone, upload bytes or perform an external effect. `settle`'s generation is a
  local callback fence, not a security credential. A real owner must authenticate
  and reconcile the operation before returning a current result.
- `preview.mjs` holds synthetic thread messages, selected thread, draft controls
  and viewport positions. The actual runtime in a product should own canonical
  messages; do not copy this toy store beside it. Thread switching fences old
  delivery callbacks while preserving each draft and unknown pending operation.
- Submit text, type a new draft before acknowledgement, then acknowledge. The
  sent snapshot is added; newer text survives. Known failure retains work.
  Unknown outcome blocks another send until an explicit simulated result.
- Add the simulated `outline.txt`. Pending/error attachment states block sends;
  mark ready to send it, fail or remove it. No local file is selected or read.
  Late callbacks cannot restore removed attachments. New attachments survive
  an older snapshot's acknowledgement; acknowledged attachment snapshots clear.
  Duplicate ready notifications preserve that admitted snapshot; genuinely changed
  upload state or a replaced file remains a distinct draft attachment.
- Send in Planning, switch to Review and type there. Resolve the previous thread
  send, then return to Planning: the result belongs there; Review's draft and
  transcript remain unchanged. A→B→A stale delivery fencing is also an executable
  model test. Current-owner reconciliation is a separate deliberate simulator path.
- Toggle read-only: typing/attachment actions/new sends stop, while an already
  admitted send can still receive its owner result. Unsupported edit/regenerate/
  branching actions are absent instead of decorative inert buttons.
- Append answers until the transcript scrolls. Scroll up, append more, then jump
  to latest. Switching threads saves and restores each reading position.
  Unknown parts render non-executable fallback text. Text uses `textContent`;
  this fixture does not implement Markdown, remote media or an HTML sanitizer.
- Keyboard: labelled input and submit; Enter submits, Shift+Enter/IME remain
  native. Status announces transitions rather than every message/token. Explicit
  attachment action replacement restores lost local focus without stealing it
  from another control. Inspect these actual browser behaviors separately.

## Product colour ownership

`palettes.mjs` defines **two fictional consuming products**, Harbor Desk and Pine
Studio. They are explicit synthetic role mappings, not real Orbyn brand tokens,
universal recommendations or an upstream theme. Select each to demonstrate that
the same shell accepts different consumer-owned mappings. Paste the real target's
existing or planned eight-role mapping only within that target's authorized work.
The preview accepts six-digit solid hex values; gradients/system colours and
other actual product tokens belong in the real framework's design system.

The fixture validates role names and syntax and refuses CSS/resource injection.
It does not approve contrast, focus visibility, full accessibility or native
parity. Use the existing colour owner to check actual foreground/background
contexts and dynamic states. Body/actions, labels, borders and focus use mapped
semantic variables; layout, type and spacing must also adapt to a real product.

## Evidence boundaries and transfer

Run the Node controls and Python wrapper for the sample state transitions. Tests
cover legitimate acknowledgements, typing races, failures/unknown outcomes,
duplicate submits, scope retirement and A→B→A callback fencing, IME policy,
attachment cancellation/replacement, read-only, safe part fallback, reading intent
and both token maps. Pure scroll decisions do not prove browser geometry,
virtualization, history-prepend anchoring, disclosure resize or screen readers.
Those remain consuming renderer tests; the method describes their ownership.

Messages and drafts are memory-only and reset on page reload. Bounds are 8000
composer characters, 16000 displayed text characters and three attachment metadata
items. The sample's controlled message-append buttons are not a production
transcript memory/history limit. No SDK, provider, Cloud, transport decoder,
real upload, durable branch/history, tool execution or production auth is tested.
Do not infer upstream runtime compatibility or live agent routing from these
helper controls. Return actual executed and unperformed checks separately.
