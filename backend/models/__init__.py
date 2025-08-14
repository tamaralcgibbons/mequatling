# backend/models/__init__.py
# Import ALL models here so SQLAlchemy sees them at startup.
# Adjust names to match your project.

from .animal import Animal              # noqa: F401
from .camp import Camp                  # noqa: F401
from .group import Group                # noqa: F401
from .vaccine import Vaccine            # noqa: F401
from .stock_ledger import StockLedger   # noqa: F401
from .vaccination import Vaccination    # noqa: F401
# add any others (stocks, users, etc.)
