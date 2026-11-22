"""FastAPI dependency providers for routes."""

from fastapi import Depends

from app.core.config import get_settings
from app.database.session import get_db

# Re-export clean dependency aliases
DbSession = Depends(get_db)
AppSettings = Depends(get_settings)
