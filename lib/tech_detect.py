import re
from collections import namedtuple

Tech = namedtuple("Tech", ["name", "version", "string", "account"])

# (name, source, pattern, version_capture_group)
_SIGS = [
    # Web servers
    ("nginx",       "server",     re.compile(r"nginx[/ ]?([\d.]+)?", re.I),             1),
    ("apache",      "server",     re.compile(r"Apache[/ ]?([\d.]+)?", re.I),            1),
    ("litespeed",   "server",     re.compile(r"LiteSpeed[/ ]?([\d.]+)?", re.I),         1),
    ("iis",         "server",     re.compile(r"Microsoft-IIS[/ ]?([\d.]+)?", re.I),     1),
    ("caddy",       "server",     re.compile(r"Caddy", re.I),                           None),
    # Languages / runtimes
    ("php",         "powered_by", re.compile(r"PHP[/ ]?([\d.]+)?", re.I),               1),
    ("python",      "powered_by", re.compile(r"Python[/ ]?([\d.]+)?", re.I),            1),
    ("ruby",        "powered_by", re.compile(r"Phusion Passenger[/ ]?([\d.]+)?|mod_ruby", re.I), 1),
    ("node.js",     "powered_by", re.compile(r"Express", re.I),                         None),
    # Frameworks
    ("django",      "powered_by", re.compile(r"Django", re.I),                          None),
    ("flask",       "powered_by", re.compile(r"Werkzeug[/ ]?([\d.]+)?", re.I),          1),
    ("laravel",     "cookie",     re.compile(r"laravel_session", re.I),                 None),
    ("rails",       "powered_by", re.compile(r"Phusion Passenger|mod_rails", re.I),     None),
    # CMS — meta generator first, then HTML content
    ("wordpress",   "meta",       re.compile(r"WordPress[/ ]?([\d.]+)?", re.I),         1),
    ("wordpress",   "html",       re.compile(r"/wp-content/|/wp-includes/", re.I),      None),
    ("drupal",      "meta",       re.compile(r"Drupal[/ ]?([\d.]+)?", re.I),            1),
    ("drupal",      "html",       re.compile(r"/sites/default/files/|Drupal\.settings", re.I), None),
    ("joomla",      "meta",       re.compile(r"Joomla![/ ]?([\d.]+)?", re.I),           1),
    ("joomla",      "html",       re.compile(r"/components/com_content|/media/jui/", re.I), None),
    ("ghost",       "meta",       re.compile(r"Ghost ([\d.]+)", re.I),                  1),
    ("mediawiki",   "meta",       re.compile(r"MediaWiki[/ ]?([\d.]+)?", re.I),         1),
]


def detect(html, headers):
    """
    html    : str  — page body (can be empty string)
    headers : dict — lowercase header name -> str value

    Returns list of Tech namedtuples, deduplicated by name.
    """
    server     = headers.get("server", "") or ""
    powered_by = (headers.get("x-powered-by", "") or headers.get("powered-by", "")) or ""
    cookie     = headers.get("set-cookie", "") or ""

    meta_gen = ""
    m = re.search(
        r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']*)["\']'
        r'|<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']generator["\']',
        html, re.I,
    )
    if m:
        meta_gen = m.group(1) or m.group(2) or ""

    sources = {
        "server":     server,
        "powered_by": powered_by,
        "meta":       meta_gen,
        "html":       html,
        "cookie":     cookie,
    }

    seen = {}
    for name, source, pattern, ver_group in _SIGS:
        if name in seen:
            continue
        text = sources.get(source, "")
        m = pattern.search(text)
        if m:
            version = None
            if ver_group and m.lastindex and m.lastindex >= ver_group:
                version = m.group(ver_group)
            seen[name] = Tech(name=name, version=version, string=None, account=None)

    return list(seen.values())
