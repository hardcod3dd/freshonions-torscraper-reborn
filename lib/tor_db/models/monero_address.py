from pony.orm import *
from tor_db.db import db
import tor_db.models.domain


class MoneroAddress(db.Entity):
    _table_ = "monero_address"
    address = Required(str, 100, unique=True)
    pages = Set(
        "Page", reverse="monero_addresses", column="monero_address", table="monero_address_link"
    )

    def domains(self):
        return select(
            d
            for d in tor_db.models.domain.Domain
            for p in d.pages
            for m in p.monero_addresses
            if m == self
        )

    @db_session
    def get_all():
        return select(
            d
            for d in tor_db.models.domain.Domain
            for p in d.pages
            for m in p.monero_addresses
            if m is not None
        )
