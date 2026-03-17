import os
from datetime import *
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Document, Date, Boolean, MetaField
from elasticsearch_dsl import analyzer, Text, Integer
from elasticsearch import serializer, exceptions
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from elasticsearch_dsl import Index
import re
import tor_text
import logging

NEVER = datetime.fromtimestamp(0)

try:
    import simplejson as json
except ImportError:
    import json


class JSONSerializerPython2(serializer.JSONSerializer):
    """Override elasticsearch library serializer to ensure it encodes utf characters during json dump.
    See original at: https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/serializer.py#L42
    A description of how ensure_ascii encodes unicode characters to ensure they can be sent across the wire
    as ascii can be found here: https://docs.python.org/2/library/json.html#basic-usage
    """

    def dumps(self, data):
        # don't serialize strings
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, default=self.default, ensure_ascii=True)
        except (ValueError, TypeError) as e:
            raise exceptions.SerializationError(data, e)


def elasticsearch_retrieve_page_by_id(page_id):
    query = Search(index="page").filter(Q("term", nid=int(page_id)))[:1]
    result = query.execute()
    if result.hits.total["value"] == 0:
        return None
    return result.hits[0]


def elasticsearch_delete_old():
    _from = NEVER
    _to = datetime.now() - timedelta(days=30)
    query = Search(index="page").filter(Q("range", visited_at={"from": _from, "to": _to}))
    result = query.delete()


def elasticsearch_pages(context, sort, page):
    result_limit = int(os.environ["RESULT_LIMIT"])
    max_result_limit = int(os.environ["MAX_RESULT_LIMIT"])
    start = (page - 1) * result_limit
    end = start + result_limit
    domain_query = Q("term", is_banned=False)
    if context["is_up"]:
        domain_query = domain_query & Q("term", is_up=True)
    if not context["show_fh_default"]:
        domain_query = domain_query & Q("term", is_crap=False)
    if not context["show_subdomains"]:
        domain_query = domain_query & Q("term", is_subdomain=False)
    if context["rep"] == "genuine":
        domain_query = domain_query & Q("term", is_genuine=True)
    if context["rep"] == "fake":
        domain_query = domain_query & Q("term", is_fake=True)

    limit = max_result_limit if context["more"] else result_limit

    has_parent_query = Q("has_parent", query=domain_query)
    if context["phrase"]:
        logging.getLogger().info("search for phrase")
        query = (
            Search(index="page")
            .query(Q("match_phrase", body_stripped=context["search"]))
        )
    else:
        logging.getLogger().info("search NOT for phrase")
        query = (
            Search(index="page")
            .query(Q("match", body_stripped=context["search"]))
        )

    query = query.highlight_options(order="score", encoder="html").highlight(
        "body_stripped"
    )[start:end]
    # query = query.source(["title", "domain_id", "created_at", "visited_at"]).params(
    #    request_cache=True
    # )

    if context["sort"] == "onion":
        query = query.sort("_id")
    elif context["sort"] == "visited_at":
        query = query.sort("-visited_at")
    elif context["sort"] == "created_at":
        query = query.sort("-created_at")
    elif context["sort"] == "last_seen":
        query = query.sort("-visited_at")

    print(query)

    return query.execute()


def is_elasticsearch_enabled():
    return (
        "ELASTICSEARCH_ENABLED" in os.environ
        and os.environ["ELASTICSEARCH_ENABLED"].lower() == "true"
    )


class DomainDocType(Document):
    title = Text(analyzer="snowball")
    created_at = Date()
    visited_at = Date()
    last_alive = Date()
    is_up = Boolean()
    is_fake = Boolean()
    is_genuine = Boolean()
    is_crap = Boolean()
    is_banned = Boolean()
    url = Text()
    is_subdomain = Boolean()
    ssl = Boolean()
    port = Integer()

    class Index:
        name = "domain"

    @classmethod
    def get_indexable(cls):
        return cls.get_model().get_objects()

    @classmethod
    def from_obj(klass, obj):
        return klass(
            meta={"id": obj.host},
            title=obj.title,
            created_at=obj.created_at,
            visited_at=obj.visited_at,
            is_up=obj.is_up,
            is_fake=obj.is_fake,
            is_genuine=obj.is_genuine,
            is_crap=obj.is_crap,
            is_banned=obj.is_banned,
            url=obj.index_url(),
            is_subdomain=obj.is_subdomain,
            ssl=obj.ssl,
            port=obj.port,
        )

    @classmethod
    def set_isup(klass, obj, is_up):
        dom = klass(meta={"id": obj.host})
        dom.update(is_up=is_up)


class PageDocType(Document):
    html_strip = analyzer(
        "html_strip",
        tokenizer="standard",
        filter=["lowercase", "stop", "snowball", "asciifolding"],
        char_filter=["html_strip"],
    )

    title = Text(analyzer="snowball")
    created_at = Date()
    visited_at = Date()
    code = Integer()
    body = Text()
    domain_id = Integer()
    body_stripped = Text(analyzer=html_strip, term_vector="with_positions_offsets")
    is_frontpage = Boolean()
    nid = Integer()

    class Index:
        name = "page"

    @classmethod
    def get_indexable(cls):
        return cls.get_model().get_objects()

    @classmethod
    def from_obj(klass, obj, body):
        return klass(
            meta={"id": obj.url, "routing": obj.domain.host},
            title=obj.title,
            created_at=obj.created_at,
            visited_at=obj.visited_at,
            is_frontpage=obj.is_frontpage,
            code=obj.code,
            domain_id=obj.domain.id,
            body=body,
            body_stripped=tor_text.strip_html(body),
            nid=obj.id,
        )


hidden_services = None

if is_elasticsearch_enabled():
    host = os.environ["ELASTICSEARCH_HOST"]
    port = os.environ.get("ELASTICSEARCH_PORT", "9200")
    connections.create_connection(
        hosts=[f"{host}:{port}"],
        serializer=JSONSerializerPython2(),
        timeout=int(os.environ["ELASTICSEARCH_TIMEOUT"]),
    )


def migrate():
    """Initialize Elasticsearch indexes with proper mappings for ES 7.x."""
    # Delete old single-index setup if it exists
    Index("hiddenservices").delete(ignore=404)
    # Create indexes with proper mappings
    DomainDocType.init()
    PageDocType.init()


logging.getLogger("elasticsearch").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
