"""CRUD для модели Table."""

from app.crud.base import CRUDBase
from app.models import Table
from app.schemas import TableCreate, TableUpdate


class TableCRUD(CRUDBase[Table, TableCreate, TableUpdate]):
    """CRUD для столов."""

    def __init__(self) -> None:
        """Инициализирует CRUD для столов."""
        super().__init__(Table)
