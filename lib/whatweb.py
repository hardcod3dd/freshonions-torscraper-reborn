from tor_db import *
from datetime import *
from tech_detect import detect as _detect


@db_session
def process(dom, html, headers):
    """
    Detect web technologies for a domain and store in web_components.
    html    : str  — page body
    headers : dict — lowercase header name -> str value
    """
    dom.whatweb_at = datetime.now()
    dom.web_components.clear()
    for tech in _detect(html, headers):
        wc = WebComponent.find_or_create(
            tech.name, account=tech.account, version=tech.version, string=tech.string
        )
        dom.web_components.add(wc)


@db_session
def process_all():
    """Re-run tech detection on all stale domains using stored header fields."""
    horizon  = datetime.now() - timedelta(weeks=1)
    horizon2 = datetime.now() - timedelta(hours=48)
    domain_ids = list(
        select(
            d.id for d in Domain if d.whatweb_at < horizon and d.last_alive > horizon2
        )
    )
    total = len(domain_ids)
    for i, did in enumerate(domain_ids, 1):
        dom = Domain.get(id=did)
        if (i % 50) == 0:
            print("Processing %d / %d" % (i, total))
        headers = {
            "server":     dom.server or "",
            "x-powered-by": dom.powered_by or "",
        }
        process(dom, "", headers)
        commit()
