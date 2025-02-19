from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")
DB = TypeVar("DB")

class AbstractDBService(ABC, Generic[T, DB]):
    """
    Абстрактный сервис для работы с базой данных.
    
    Args:
        T: Тип возвращаемых данных
        DB: Тип подключения к базе данных
    """
    
    def __init__(self, db_client: DB):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_client: Клиент для подключения к БД
        """
        self.db_client = db_client


    @abstractmethod
    async def get_by_id(self, object_id: str) -> Optional[T]:
        """Получение объекта по ID."""
        raise NotImplementedError
        
        
    @abstractmethod
    async def search(self, query: str, page_number: int, page_size: int) -> List[T]:
        """Поиск объектов по заданному запросу."""
        raise NotImplementedError