#!/usr/bin/env python3
"""Collect one job's icons into a git-ignored folder, unmodified apart from sanitising.

Usage:
  python3 fetch_icons.py OUTDIR SPEC [SPEC ...] [--allow-network]

Without --allow-network nothing is fetched: every spec gets a neutral pictogram
from assets/generic. Pass the flag only when the user asked for logos and network
access is available. With it, OUTDIR must be outside Git or ignored by Git.

Spec forms (add ~KIND to any of them to choose the fallback pictogram, default box):
  name               slug equals name              hono~server
  name:slug          different slug                betterauth:better-auth
  name=URL           explicit https URL            orpc=https://orpc.example/logo.webp
  name:aws/Service   AWS's own icon                lambda:aws/lambda
  name:lucide/icon   Lucide pictogram              cron:lucide/clock
  name:generic/kind  bundled pictogram, no fetch   client:generic/user

Sources tried for a slug: svgl, devicon, gilbarbara/logos. svgl must match the title
exactly, because its search is fuzzy and a loose hit would ship another brand's logo.
simple-icons stays out: its glyphs are monochrome redraws, not official marks.

Writes OUTDIR/<name>.<ext>, OUTDIR/<name>_dark.<ext> when the source has a dark
variant, and OUTDIR/manifest.json, which records each icon's source and any fallback.
Exits 0 when every spec resolved, including to a pictogram (each one prints FALLBACK);
exits 2 on a bad spec, an unusable OUTDIR or a corrupt manifest.
"""
import argparse
import http.client
import io
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_guard import NotIgnored, require_ignored  # noqa: E402
from sanitise_svg import MAX_SVG_BYTES, UnsafeSvg, sanitise_svg  # noqa: E402

GENERIC = Path(__file__).resolve().parents[1]/'assets/generic'
DEFAULT_PICTOGRAM = 'box'
MAX_ICON_BYTES = MAX_SVG_BYTES
MAX_PACKAGE_BYTES = 256 * 1024 * 1024
SOCKET_TIMEOUT = 10
ICON_DEADLINE = 30
PACKAGE_DEADLINE = 180
UA = {'User-Agent': 'stack-diagram-skill'}
NAME_RE = re.compile(r'[A-Za-z0-9_-]+')  # Becomes a filename and an %%ICON_<name>%% token.
SLUG_RE = re.compile(r'[A-Za-z0-9._+-]+')  # Goes into a URL path.
ICON_SUFFIXES = {'.svg', '.png', '.webp', '.jpg', '.jpeg'}
FETCH_ERRORS = (urllib.error.URLError, OSError, http.client.HTTPException, ValueError,
                zipfile.BadZipFile, KeyError, RecursionError)
NAT64 = ipaddress.ip_network('64:ff9b::/96')
PAINT_REMOVALS = {f'attribute:{name}' for name in ('fill', 'stroke', 'stop-color', 'color', 'filter', 'mask', 'clip-path')}

AWS_ICONS_PAGE = 'https://aws.amazon.com/architecture/icons/'
AWS_PACKAGE_RE = re.compile(r"""(?:https:)?//[\w.-]+\.awsstatic\.com/[^"'\s]+/Icon-package_[^"'\s/]+\.zip""")
AWS_ICON_RE = re.compile(r'Architecture-Service-Icons_[^/]+/[^/]+/64/Arch_(.+)_64\.svg'
                         r'|Architecture-Group-Icons_[^/]+/(.+)_32\.svg'
                         r'|Resource-Icons_[^/]+/Res_General-Icons/Res_48_Light/Res_(.+)_48_Light\.svg')
AWS_ALIASES = {
    's3': 'Amazon-Simple-Storage-Service', 'glacier': 'Amazon-Simple-Storage-Service-Glacier',
    'sqs': 'Amazon-Simple-Queue-Service', 'sns': 'Amazon-Simple-Notification-Service',
    'ses': 'Amazon-Simple-Email-Service', 'ecs': 'Amazon-Elastic-Container-Service',
    'eks': 'Amazon-Elastic-Kubernetes-Service', 'ecr': 'Amazon-Elastic-Container-Registry',
    'elb': 'Elastic-Load-Balancing', 'alb': 'Elastic-Load-Balancing', 'nlb': 'Elastic-Load-Balancing',
    'iam': 'AWS-Identity-and-Access-Management', 'kms': 'AWS-Key-Management-Service',
    'msk': 'Amazon-Managed-Streaming-for-Apache-Kafka', 'opensearch': 'Amazon-OpenSearch-Service',
    'vpc': 'Virtual-private-cloud-VPC',
}


class FetchRefused(ValueError):
    """A policy limit stopped the request; never retried against the same URL."""


def is_public(address):
    """True only for a global address, looking through forms that embed an IPv4 address."""
    ip = ipaddress.ip_address(str(address).split('%')[0])
    if ip.version == 6:
        for inner in (ip.ipv4_mapped, ip.sixtofour, ip.teredo[1] if ip.teredo else None,
                      ipaddress.IPv4Address(int(ip) & 0xffffffff) if ip in NAT64 else None):
            if inner is not None and not is_public(inner):
                return False
        if ip in NAT64:
            return True  # 64:ff9b::/96 is not "global" itself; the embedded address decides.
    return ip.is_global


def literal_address(host):
    """The address a host spells directly, including decimal, hex and octal IPv4 forms."""
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    try:
        return ipaddress.ip_address(socket.inet_ntoa(socket.inet_aton(host)))
    except OSError:
        return None


def require_public_host(host):
    """Refuse a fetch or redirect that lands on this machine or a private network."""
    literal = literal_address(host)
    if literal is not None:
        if not is_public(literal):
            raise FetchRefused(f'refused non-public address: {host}')
        return
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, 443)}
    except OSError:
        return  # An unknown name cannot connect, and require_public_peer checks what does.
    if not all(is_public(address) for address in addresses):
        raise FetchRefused(f'refused non-public address: {host}')


def require_public_peer(sock):
    """Check the address really connected to, so a second DNS answer cannot move the request."""
    peer = sock.getpeername()[0]
    if not is_public(peer):
        sock.close()
        raise FetchRefused(f'refused non-public address: {peer}')


def require_https(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname:
        raise FetchRefused(f'refused non-https URL: {url}')
    if parts.username or parts.password:
        raise FetchRefused(f'refused URL with embedded credentials: {parts.hostname}')
    require_public_host(parts.hostname)


# Pinned, so a source changing its files cannot change what a diagram fetches.
LUCIDE_VERSION = '1.66.0'
DEVICON_VERSION = 'v2.18.0'
LOGOS_REVISION = 'd6960edc1b7309d392c76e40d3a320df7f9ff85c'


class HttpsRedirects(urllib.request.HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


FETCH_STATE = threading.local()


class GuardedConnection(http.client.HTTPSConnection):
    def connect(self):
        super().connect()
        require_public_peer(self.sock)
        sockets = getattr(FETCH_STATE, 'sockets', None)
        if sockets is not None:
            sockets.append(self.sock)


class GuardedHttps(urllib.request.HTTPSHandler):
    handler_order = 510  # After a test's stub, which answers first.

    def https_open(self, req):
        return self.do_open(GuardedConnection, req, context=self._context)


def make_opener(*handlers):
    return urllib.request.build_opener(HttpsRedirects, GuardedHttps, *handlers)


OPENER = make_opener()


def cut_off(sockets):
    """Blocked reads return at once; a drip of bytes would otherwise reset the socket timeout."""
    for sock in sockets:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


def get(url, limit=MAX_ICON_BYTES, deadline=ICON_DEADLINE):
    """Bytes of an https URL, bounded by size and by total wall-clock time, headers included."""
    require_https(url)
    expires = time.monotonic() + deadline
    request = urllib.request.Request(url, headers=UA)
    FETCH_STATE.sockets = sockets = []
    timer = threading.Timer(deadline, cut_off, [sockets])
    timer.daemon = True
    timer.start()
    try:
        with OPENER.open(request, timeout=SOCKET_TIMEOUT) as response:
            declared = response.headers.get('Content-Length')
            if declared and declared.isdigit() and int(declared) > limit:
                raise FetchRefused(f'{url} declares {declared} bytes, limit {limit}')
            read = getattr(response, 'read1', response.read)  # read() blocks until 64 KiB arrive.
            body = bytearray()
            while chunk := read(64 * 1024):
                body += chunk
                if len(body) > limit:
                    raise FetchRefused(f'{url} exceeds the {limit} byte limit')
                if time.monotonic() > expires:
                    raise FetchRefused(f'{url} exceeded the {deadline}s deadline')
    except (OSError, http.client.HTTPException) as error:
        if time.monotonic() > expires:
            raise FetchRefused(f'{url} exceeded the {deadline}s deadline') from error
        raise
    finally:
        timer.cancel()
        FETCH_STATE.sockets = None
    if time.monotonic() > expires:
        raise FetchRefused(f'{url} exceeded the {deadline}s deadline')
    return bytes(body)


def classify(raw):
    """Decide the type from the bytes; a URL's suffix says nothing about its content."""
    if raw[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return 'webp'
    if raw[:3] == b'\xff\xd8\xff':
        return 'jpg'
    head = raw[:2048].lstrip(b'\xef\xbb\xbf \t\r\n').lower()
    if head.startswith(b'<svg') or (head.startswith((b'<?xml', b'<!doctype svg', b'<!--')) and b'<svg' in raw[:8192].lower()):
        return 'svg'
    return None


def admit(raw):
    """Return (bytes, ext, removed) ready to save, or raise when the icon must be skipped."""
    if len(raw) < 50:
        raise FetchRefused('body too small to be an icon')
    ext = classify(raw)
    if ext is None:
        raise FetchRefused('body is not an image')
    if ext != 'svg':
        return raw, ext, []
    clean, removed = sanitise_svg(raw)
    if 'style' in removed or PAINT_REMOVALS & set(removed):
        raise UnsafeSvg('styling reached outside the file; removing it would recolour the mark')
    return clean, ext, removed


def white_fill(raw):
    """True only when the mark is white overall: a white detail on a coloured logo is not."""
    paints = re.findall(r'(?:fill|stroke|stop-color)[=:]\s*"?([#a-zA-Z][^";\s>]*)', raw.decode('utf-8', 'ignore'))
    white = coloured = False
    for paint in paints:
        paint = paint.strip().lower()
        if paint in ('none', 'transparent', 'currentcolor') or paint.startswith('url('):
            continue
        if re.fullmatch(r'#f{3}(f{3})?|white', paint):
            white = True
        else:
            coloured = True
    return white and not coloured


def norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def svgl_lookup(slug):
    """(url, dark url or None) on an exact title match, else None."""
    queries = [slug, re.sub(r'[-_.]+', ' ', slug).strip()]
    targets = {norm(slug)}
    if len(slug) > 4 and slug.endswith('js'):
        queries.append(slug[:-2])
        targets.add(norm(slug[:-2]))
    for query in dict.fromkeys(queries):
        try:
            items = json.loads(get(f'https://api.svgl.app?search={urllib.parse.quote(query)}'))
        except FETCH_ERRORS:
            continue
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict) or norm(str(item.get('title', ''))) not in targets:
                continue
            route = item.get('route')
            if isinstance(route, dict):  # Tiles are white in both themes, so light goes first.
                light, dark = route.get('light'), route.get('dark')
                if isinstance(light, str):
                    return light, dark if isinstance(dark, str) else None
                return (dark, None) if isinstance(dark, str) else None
            return (route, None) if isinstance(route, str) else None
    return None


class AwsPackage:
    """AWS's icon package, held in memory for this run and never written to disk."""

    def __init__(self):
        self.archive = None
        self.index = {}

    def load(self):
        if self.archive:
            return
        page = get(AWS_ICONS_PAGE).decode('utf-8', 'ignore')
        link = AWS_PACKAGE_RE.search(page)
        if not link:
            raise OSError(f'no Icon-package link on {AWS_ICONS_PAGE}')
        url = urllib.parse.urljoin(AWS_ICONS_PAGE, link.group())
        self.archive = zipfile.ZipFile(io.BytesIO(get(url, MAX_PACKAGE_BYTES, PACKAGE_DEADLINE)))
        members = set(self.archive.namelist())
        for member in sorted(members):
            match = AWS_ICON_RE.fullmatch(member)
            if match:  # The General- prefix keeps General-Shield from taking AWS-Shield's short name.
                name = match.group(1) or match.group(2) or f'General-{match.group(3)}'
                dark = member.replace('_Light', '_Dark') if match.group(3) else member[:-4]+'_Dark.svg'
                self.index.setdefault(norm(name), (name, member, dark if dark in members else None))

    def read(self, member):
        info = self.archive.getinfo(member)
        if info.file_size > MAX_ICON_BYTES:  # zipfile stops at this size, and a lie fails the CRC.
            raise FetchRefused(f'{member} exceeds the {MAX_ICON_BYTES} byte limit')
        return self.archive.read(info)

    def sources(self, query):
        """Exact name or acronym, AWS-/Amazon- prefix optional. A miss lists every name."""
        try:
            self.load()
        except FETCH_ERRORS as error:
            print(f'AWS  icon package unavailable: {error}')
            return []
        wanted = norm(AWS_ALIASES.get(norm(query), query))
        hit = self.index.get(wanted) or next(
            (value for key, value in self.index.items() if re.sub(r'^(aws|amazon)', '', key) == wanted), None)
        if hit:
            return [('aws', f'aws:{hit[1]}', f'aws:{hit[2]}' if hit[2] else None)]
        print(f"AWS  {query!r} is not in the package. Names: {', '.join(sorted(v[0] for v in self.index.values()))}")
        return []


AWS = AwsPackage()


def read(url):
    return AWS.read(url[4:]) if url.startswith('aws:') else get(url)


def sources(slug):
    if slug.startswith('lucide/'):
        return [('lucide', f'https://cdn.jsdelivr.net/npm/lucide-static@{LUCIDE_VERSION}/icons/{slug[7:]}.svg', None)]
    if slug.startswith('aws/'):
        return AWS.sources(slug[4:])
    if norm(slug) in ('aws', 'amazonwebservices'):
        return AWS.sources('AWS-Cloud-logo')
    if slug[:4].lower() == 'aws-':
        return AWS.sources(slug[4:])
    found = svgl_lookup(slug)
    return ([('svgl', *found)] if found else []) + [
        ('devicon', f'https://cdn.jsdelivr.net/gh/devicons/devicon@{DEVICON_VERSION}/icons/{slug}/{slug}-original.svg', None),
        ('gilbarbara', f'https://cdn.jsdelivr.net/gh/gilbarbara/logos@{LOGOS_REVISION}/logos/{slug}-icon.svg', None),
        ('gilbarbara', f'https://cdn.jsdelivr.net/gh/gilbarbara/logos@{LOGOS_REVISION}/logos/{slug}.svg', None),
    ]


def parse_spec(spec):
    """Split a spec into (name, kind of spec, value, fallback pictogram); raise ValueError."""
    kinds = {path.stem for path in GENERIC.glob('*.svg')}
    head, _, tail = spec.rpartition('~')
    fallback = DEFAULT_PICTOGRAM
    if head and tail in kinds:
        spec, fallback = head, tail
    if '=' in spec:
        name, _, value = spec.partition('=')
        kind = 'url'
    else:
        name, _, value = spec.partition(':')
        kind = 'slug'
        value = value or name.lower()
        if value.startswith('generic/'):
            kind, value = 'generic', value[8:]
            if value not in kinds:
                raise ValueError(f'unknown pictogram {value!r}; have {", ".join(sorted(kinds))}')
        elif not all(SLUG_RE.fullmatch(part) for part in value.split('/')) or value.count('/') > 1:
            raise ValueError(f'invalid slug {value!r}')
    if not NAME_RE.fullmatch(name):
        raise ValueError(f'icon name {name!r} must match [A-Za-z0-9_-]+')
    if head and tail not in kinds and '=' not in spec:
        raise ValueError(f'unknown fallback pictogram {tail!r}')
    if fallback == DEFAULT_PICTOGRAM and name in kinds:
        fallback = name
    return name, kind, value, fallback


def write_atomic(path, data):
    partial = path.with_name(f'.{path.name}.{os.getpid()}.partial')
    partial.write_bytes(data)
    os.replace(partial, path)


def store(outdir, name, data, ext):
    """A re-fetch must not leave an older file with another suffix for build.py to find."""
    for old in [*outdir.glob(f'{name}.*'), *outdir.glob(f'{name}_dark.*')]:
        if old.suffix in ICON_SUFFIXES:
            old.unlink()
    path = outdir/f'{name}.{ext}'
    write_atomic(path, data)
    return path


def use_pictogram(outdir, name, kind):
    data = (GENERIC/f'{kind}.svg').read_bytes()
    path = store(outdir, name, data, 'svg')
    return {'source': 'generic', 'pictogram': kind, 'file': path.name, 'bytes': len(data)}


def fetch_one(outdir, name, tries):
    """Save the first source that passes every check. Returns (entry or None, last reason)."""
    reason = 'no source has it'
    for source, url, dark_url in tries:
        try:
            raw = read(url)
            if source == 'lucide':  # A concept icon, not a logo, so matching the ink is allowed.
                raw = raw.replace(b'stroke="currentColor"', b'stroke="#3d4660"')
                raw = raw.replace(b'stroke-width="2"', b'stroke-width="1.7"')
            data, ext, removed = admit(raw)
        except FETCH_ERRORS as error:
            reason = str(error)
            if isinstance(error, (FetchRefused, UnsafeSvg)):
                print(f'REFUSED {name}: {error}')
            continue
        path = store(outdir, name, data, ext)
        entry = {'source': source, 'url': url, 'file': path.name, 'bytes': len(data)}
        if removed:
            entry['sanitised'] = removed
        if ext == 'svg' and white_fill(data):
            entry['white_fill'] = True
            entry['note'] = ('white fill detected. It may be an inner detail on a coloured logo: inspect '
                             'the SVG and use a dark tile only for a mark that is white overall. Never recolour.')
        if dark_url:
            try:
                dark, dark_ext, _ = admit(read(dark_url))
            except FETCH_ERRORS:
                dark = None
            if dark:
                dark_path = outdir/f'{name}_dark.{dark_ext}'
                write_atomic(dark_path, dark)
                entry['dark_file'] = dark_path.name
        return entry, reason
    return None, reason


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('outdir', type=Path)
    parser.add_argument('specs', nargs='+')
    parser.add_argument('--allow-network', action='store_true',
                        help='fetch logos; use only when the user asked for them')
    args = parser.parse_args(argv)
    try:
        specs = [parse_spec(spec) for spec in args.specs]
    except ValueError as error:
        parser.exit(2, f'{error}\n')
    args.outdir.mkdir(parents=True, exist_ok=True)
    outdir = args.outdir.resolve()
    if args.allow_network:
        try:
            require_ignored(outdir)
        except NotIgnored as error:
            raise SystemExit(str(error)) from error
    manifest_path = outdir/'manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    except ValueError as error:
        parser.exit(2, f'{manifest_path} is corrupt: {error}\n')
    if not isinstance(manifest, dict):
        parser.exit(2, f'{manifest_path} is corrupt: expected an object\n')
    fallbacks = []
    for name, kind, value, fallback in specs:
        if kind == 'generic':
            manifest[name] = use_pictogram(outdir, name, value)
            print(f'OK   {name:<16} generic pictogram {value}')
            continue
        if not args.allow_network:
            entry, reason = None, 'network not allowed for this run'
        else:
            tries = [('explicit', value, None)] if kind == 'url' else sources(value)
            entry, reason = fetch_one(outdir, name, tries)
        if entry:
            flags = ' [WHITE FILL: check for a dark tile]' if entry.get('white_fill') else ''
            flags += f" [sanitised: {', '.join(entry['sanitised'])}]" if entry.get('sanitised') else ''
            print(f"OK   {name:<16} {entry['source']:<12} {entry['bytes']:>7}B{flags}")
        else:
            entry = use_pictogram(outdir, name, fallback)
            entry.update(fallback=True, reason=reason)
            fallbacks.append(name)
            print(f'FALLBACK {name}: neutral {fallback} pictogram ({reason})')
        manifest[name] = entry
    write_atomic(manifest_path, (json.dumps(manifest, indent=2)+'\n').encode())
    if fallbacks:
        print(f"{len(fallbacks)} of {len(specs)} icons are neutral pictograms, not logos: {', '.join(fallbacks)}. "
              'Tell the user. To retry one, pass name=URL with the official file.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
