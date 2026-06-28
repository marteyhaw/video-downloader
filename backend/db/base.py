"""Declarative base for ORM models.

Split out from ``session`` so ``models`` (which needs ``Base``) and
``session`` (which needs ``models`` only inside ``init_db``) no longer import
each other, breaking the previous import cycle.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
