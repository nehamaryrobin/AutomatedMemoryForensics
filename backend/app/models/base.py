from typing import Any
from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True
    id: Any
