from .sharding_manager import ShardingManager
from .sqlite_disk_repository import SqliteDiskRepository
from .sqlite_object_repository import SqliteObjectRepository


class StorageLibrary:
    def __init__(self, db_path: str):
        # Создаёт библиотеку с SQLite-хранилищем.
        self.disk_repo = SqliteDiskRepository(db_path)
        self.obj_repo = SqliteObjectRepository(db_path)
        self.manager = ShardingManager(self.disk_repo, self.obj_repo)

    def register_disk(
        self, mount_point: str, total_space: int, status: str = "available"
    ) -> int:
        # Добавляет новый диск в систему. Возвращает ID диска.
        return self.manager.register_disk(mount_point, total_space, status)

    def get_disk_info(self, disk_id: int) -> dict | None:
        # Возвращает информацию о диске по ID.
        return self.manager.get_disk_info(disk_id)

    def get_all_disks(self) -> list[dict]:
        # Возвращает список всех дисков.
        return self.manager.get_all_disks()

    def create_object(self, initial_size: int, obj_id: str | None = None) -> str:
        # Создаёт объект с резервированием места.
        return self.manager.create_object(obj_id, initial_size)

    def complete_object(self, obj_id: str) -> None:
        # После вызова объект становится доступным для чтения.
        self.manager.complete_object(obj_id)

    def delete_object(self, obj_id: str) -> None:
        # Удаляет объект и освобождает всё занятое им место.
        self.manager.delete_object(obj_id)

    def expand_reserved(self, obj_id: str, extra_bytes: int) -> bool:
        # Расширяет зарезервированное место для объекта.
        return self.manager.expand_reserved(obj_id, extra_bytes)

    def cleanup_stale(self, older_than_seconds: int) -> int:
        # Возвращает количество удалённых объектов.
        return self.manager.cleanup_stale(older_than_seconds)

    def close(self) -> None:
        # Закрывает соединения с базой данных.
        self.disk_repo.close()
        self.obj_repo.close()
        pass

    def update_disk_status(self, disk_id: int, status: str) -> None:
        # Обновляет статус диска (available, readonly, unavailable)
        self.manager.update_disk_status(disk_id, status)

    def set_object_size(self, obj_id: str, actual_size: int) -> None:
        # Обновляет фактический размер объекта и used_space на диске.
        self.manager.set_object_size(obj_id, actual_size)
