#!/usr/bin/env python3
"""Screenshot a built diagram with an existing Chrome over a DevTools pipe.

Usage:
  python3 render_png.py IN.html OUT.png [--selector .page] [--scale 2] [--full-page] [--single]

By default writes OUT.png (light) and OUT-dark.png (data-theme="dark"), with square
corners in the screenshot only. The default .page keeps the title, legend and credit
with the drawing, so the image explains its edges and names its icon sources on its
own. --selector .canvas captures the bare drawing. --single captures the document as
authored.

Browser, first match wins: CHROME_PATH; the browser of a Python Playwright that is
already installed; Chrome or Chromium on PATH; the standard macOS install; an existing
Playwright browser cache. This script installs nothing and downloads nothing. It runs
the browser with its sandbox on, a throwaway profile and name resolution disabled,
and fails if the page requests anything over the network. POSIX only, because the
pipe needs inherited file descriptors.
"""
import argparse
import base64
import fcntl
import glob
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_guard import require_ignored  # noqa: E402

LOGO_MARKER = '<meta name="stack-diagram-logos" content="fetched">'

TIMEOUT = 30
SQUARE_CORNERS = ('.scroller{border-radius:0!important;border:none!important}'
                  '.canvas{border-radius:0!important}')
BINARIES = ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome')
INSTALLED = ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
             '/Applications/Chromium.app/Contents/MacOS/Chromium')
PLAYWRIGHT_CACHES = (
    '~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*',
    '~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome',
)


class RenderError(RuntimeError):
    pass


def playwright_browser():
    """Ask an installed Python Playwright where its browser is; never run its installer."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as driver:
            return driver.chromium.executable_path
    except Exception:  # A broken driver only means this candidate is unavailable.
        return None


def find_browser():
    explicit = os.environ.get('CHROME_PATH')
    if explicit:
        if not os.access(explicit, os.X_OK):
            raise RenderError(f'CHROME_PATH is not an executable file: {explicit}')
        return explicit
    candidates = [playwright_browser(), *map(shutil.which, BINARIES), *INSTALLED]
    for pattern in PLAYWRIGHT_CACHES:
        candidates += sorted(glob.glob(os.path.expanduser(pattern)), reverse=True)
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RenderError('no Chrome found. Set CHROME_PATH to an existing Chrome or Chromium binary.')


def high_fd(fd):
    """Move a pipe end above 3 and 4 so the child's dup2 calls cannot collide."""
    moved = fcntl.fcntl(fd, fcntl.F_DUPFD, 10)
    os.close(fd)
    return moved


class Browser:
    """One owned Chrome process. Chrome reads commands on fd 3 and answers on fd 4."""

    def __init__(self, binary):
        self.profile = tempfile.mkdtemp(prefix='stack-diagram-chrome-')
        self.buffer = b''
        self.next_id = 0
        self.events = []
        commands_read, self.commands = map(high_fd, os.pipe())
        self.replies, replies_write = map(high_fd, os.pipe())

        def wire():
            os.dup2(commands_read, 3)
            os.dup2(replies_write, 4)

        self.process = subprocess.Popen(
            [binary, '--headless=new', '--remote-debugging-pipe', f'--user-data-dir={self.profile}',
             '--no-first-run', '--no-default-browser-check', '--disable-extensions',
             '--disable-background-networking', '--disable-sync', '--hide-scrollbars',
             '--font-render-hinting=none', '--host-resolver-rules=MAP * ~NOTFOUND', 'about:blank'],
            preexec_fn=wire, pass_fds=(3, 4), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(commands_read)
        os.close(replies_write)

    def read_message(self, expires):
        while b'\0' not in self.buffer:
            remaining = expires - time.monotonic()
            if remaining <= 0:
                raise RenderError(f'Chrome did not answer within {TIMEOUT}s')
            if not select.select([self.replies], [], [], remaining)[0]:
                continue
            chunk = os.read(self.replies, 1024 * 1024)
            if not chunk:
                raise RenderError(f'Chrome exited early with status {self.process.poll()}')
            self.buffer += chunk
        message, _, self.buffer = self.buffer.partition(b'\0')
        return json.loads(message)

    def send(self, method, session=None, **params):
        self.next_id += 1
        request = {'id': self.next_id, 'method': method, 'params': params}
        if session:
            request['sessionId'] = session
        payload = json.dumps(request).encode()+b'\0'
        while payload:
            payload = payload[os.write(self.commands, payload):]
        expires = time.monotonic()+TIMEOUT
        while True:
            message = self.read_message(expires)
            if message.get('id') == self.next_id:
                if 'error' in message:
                    raise RenderError(f"{method}: {message['error'].get('message')}")
                return message['result']
            self.events.append(message)

    def wait_for(self, method):
        expires = time.monotonic()+TIMEOUT
        while True:
            for event in self.events:
                if event.get('method') == method:
                    return
            self.events.append(self.read_message(expires))

    def remote_requests(self):
        urls = [event['params']['request']['url'] for event in self.events
                if event.get('method') == 'Network.requestWillBeSent']
        urls += [event['params']['url'] for event in self.events if event.get('method') == 'Network.webSocketCreated']
        return sorted({url for url in urls if url.startswith(('http:', 'https:', 'ws:', 'wss:'))})

    def close(self):
        try:
            self.send('Browser.close')
        except (OSError, RenderError, ValueError):
            pass
        for fd in (self.commands, self.replies):
            os.close(fd)
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(10)
        shutil.rmtree(self.profile, ignore_errors=True)


def evaluate(browser, session, expression):
    result = browser.send('Runtime.evaluate', session, expression=expression,
                          awaitPromise=True, returnByValue=True)
    if 'exceptionDetails' in result:
        raise RenderError(f"page evaluation failed: {result['exceptionDetails'].get('text')}")
    return result['result'].get('value')


def shoot(browser, session, selector, full_page, path):
    """Measure at capture time, because a theme change can reflow the page."""
    scope = 'document.documentElement' if full_page else f'document.querySelector({json.dumps(selector)})'
    rect = evaluate(browser, session, f"""(() => {{
        const el = {scope};
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const w = {'el.scrollWidth' if full_page else 'r.width'}, h = {'el.scrollHeight' if full_page else 'r.height'};
        return {{x: r.left + scrollX, y: r.top + scrollY, width: w, height: h}};
    }})()""")
    if not rect or rect['width'] <= 0 or rect['height'] <= 0:
        raise RenderError(f'selector {selector!r} matched nothing visible')
    shot = browser.send('Page.captureScreenshot', session, format='png', captureBeyondViewport=True,
                        clip={**rect, 'scale': 1})
    return path, base64.b64decode(shot['data'])


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f'.{path.name}.{os.getpid()}.partial')
    partial.write_bytes(data)
    os.replace(partial, path)
    print(f'rendered {path}')


def warn_missing_japanese_font(source):
    """Without a Japanese face, Linux fallback draws Chinese glyph variants."""
    if 'lang="ja"' not in source[:400] or not shutil.which('fc-list'):
        return
    fonts = subprocess.run(['fc-list', ':lang=ja'], capture_output=True, text=True).stdout
    if 'Sans' not in fonts:
        print('WARNING: no Japanese sans font on this host. Japanese labels will show Chinese '
              'glyph variants. Render on a host that has one.')


def render(source, out, selector, scale, full_page, single, allow_tracked=False):
    text = source.read_text(encoding='utf-8')
    warn_missing_japanese_font(text)
    if LOGO_MARKER in text and not allow_tracked:
        require_ignored(out.resolve().parent)
    shots = []
    browser = Browser(find_browser())
    try:
        target = browser.send('Target.createTarget', url='about:blank')['targetId']
        session = browser.send('Target.attachToTarget', targetId=target, flatten=True)['sessionId']
        for domain in ('Page', 'Runtime', 'Network'):
            browser.send(f'{domain}.enable', session)
        metrics = {'height': 1000, 'deviceScaleFactor': scale, 'mobile': False}
        browser.send('Emulation.setDeviceMetricsOverride', session, width=1200, **metrics)
        browser.send('Page.navigate', session, url=source.as_uri())
        browser.wait_for('Page.loadEventFired')
        width = evaluate(browser, session, "document.querySelector('.canvas')?.offsetWidth ?? 0")
        if width + 100 > 1200:  # .scroller clips a canvas wider than the viewport.
            browser.send('Emulation.setDeviceMetricsOverride', session, width=int(width)+100, **metrics)
        evaluate(browser, session, f"""(async () => {{
            const style = document.createElement('style');
            style.textContent = {json.dumps(SQUARE_CORNERS)};
            document.head.append(style);
            await document.fonts.ready;
        }})()""")
        if single:
            shots.append(shoot(browser, session, selector, full_page, out))
        else:
            for theme, path in ((None, out), ('dark', out.with_name(f'{out.stem}-dark{out.suffix}'))):
                action = f"setAttribute('data-theme','{theme}')" if theme else "removeAttribute('data-theme')"
                evaluate(browser, session, f"""(async () => {{
                    document.documentElement.{action};
                    await new Promise(requestAnimationFrame);
                    await new Promise(requestAnimationFrame);
                }})()""")
                shots.append(shoot(browser, session, selector, full_page, path))
        remote = browser.remote_requests()
        if remote:
            raise RenderError(f"page is not self-contained, it requested: {', '.join(remote)}")
        for path, data in shots:  # Nothing is written until the page is known to be clean.
            save(path, data)
    finally:
        browser.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--selector', default='.page')
    parser.add_argument('--scale', type=float, default=2)
    parser.add_argument('--full-page', action='store_true')
    parser.add_argument('--single', action='store_true')
    parser.add_argument('--allow-tracked', action='store_true',
                        help='write fetched logos to a folder Git may commit; only when the user asked')
    args = parser.parse_args(argv)
    if not 0.5 <= args.scale <= 4:
        parser.exit(2, '--scale must be between 0.5 and 4\n')
    if not args.source.is_file():
        parser.exit(2, f'no such file: {args.source}\n')
    try:
        render(args.source.resolve(), args.out, args.selector, args.scale, args.full_page, args.single, args.allow_tracked)
    except (OSError, RenderError, ValueError) as error:
        parser.exit(1, f'render failed: {error}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
