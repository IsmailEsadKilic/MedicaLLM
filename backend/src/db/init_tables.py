"""Initialize all PostgreSQL tables."""
import logging
from sqlalchemy import text, inspect

from .sql_client import get_engine, get_session
from .sql_models import Base

from logging import getLogger

logger = getLogger(__name__)
