"""Modelos SQLAlchemy. Importar o pacote registra todas as tabelas em `Base.metadata`."""

from app.models.favorite import Favorite
from app.models.harvest_run import HarvestRun
from app.models.oai_record import OaiRecord
from app.models.search_history import SearchHistory
from app.models.security_event import SecurityEvent
from app.models.user import User

__all__ = ["Favorite", "HarvestRun", "OaiRecord", "SearchHistory", "SecurityEvent", "User"]
