from .disk_repository_protocol import DiskRepositoryProtocol
from .object_repository_protocol import ObjectRepositoryProtocol
from .exceptions import (DiskNotFoundError, NotEnoughSpaceError, DiskUnavailableError, ObjectNotFoundError, ObjectAlreadyExistsError)

class ShardingManager:
    def __init__(self, disk_repo: DiskRepositoryProtocol, obj_repo: ObjectRepositoryProtocol):
        self.disk_repo = disk_repo
        self.obj_repo = obj_repo


    def register_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        return self.disk_repo.add_disk(mount_point, total_space, status)

    def update_disk_status(self, disk_id: int, status: str) -> None:
        self.disk_repo.update_disk_status(disk_id, status)


    def allocate_disk(self, required_bytes: int) -> int:
        disks = self.disk_repo.get_all_disks()
        for disk in disks:
            if disk["status"] != "available":
                continue
            free = disk["total_space"] - (disk["used_space"] + disk["reserved_space"])
            if free >= required_bytes:
                return disk["id"]
        raise NotEnoughSpaceError("Нет подходящего диска с достаточным свободным местом")
    
    
    def reserve_space(self, disk_id: int, bytes_to_reserve: int) -> None:
        disk = self.disk_repo.get_disk(disk_id)
        if disk is None:
            raise DiskNotFoundError(f"Диск {disk_id} не найден")
        if disk["status"] != "available":
            raise DiskUnavailableError(f"Диск {disk_id} недоступен для записи (статус: {disk['status']})")
        self.disk_repo.update_disk_space(disk_id, used_delta=0, reserved_delta=bytes_to_reserve)


    def release_space(self, disk_id: int, used_bytes: int, reserved_bytes: int) -> None:
        self.disk_repo.update_disk_space(disk_id, used_delta=-used_bytes, reserved_delta=-reserved_bytes)


    def create_object(self, obj_id: str, initial_size: int) -> None:
        existing = self.obj_repo.get_object(obj_id)
        if existing is not None:
            raise ObjectAlreadyExistsError(f"Объект {obj_id} уже существует")


        disk_id = self.allocate_disk(initial_size)
        self.reserve_space(disk_id, initial_size)
        self.obj_repo.add_object(obj_id, disk_id, initial_size)


    def complete_object(self, obj_id: str) -> None:
        obj = self.obj_repo.get_object(obj_id)
        if obj is None:
            return
        # Освобождаем reserved_space на диске
        self.disk_repo.update_disk_space(
            obj["disk_id"],
            used_delta=0,
            reserved_delta=-obj["reserved_size"]
        )
        # Обновляем объект
        self.obj_repo.update_object(obj_id, is_completed=1, reserved_size=0)


    def delete_object(self, obj_id: str) -> None:
        obj = self.obj_repo.get_object(obj_id)
        if obj is None:
            return
        # Освобождаем used_space и reserved_space
        self.disk_repo.update_disk_space(
            obj["disk_id"],
            used_delta=-obj["current_size"],
            reserved_delta=-obj["reserved_size"]
        )
        self.obj_repo.delete_object(obj_id)


    def cleanup_stale(self, older_than_seconds: int) -> int:
        stale_objects = self.obj_repo.get_incomplete_objects(older_than_seconds)
        count = 0
        for obj in stale_objects:
            # Освобождаем место
            self.disk_repo.update_disk_space(
                obj["disk_id"],
                used_delta=-obj["current_size"],
                reserved_delta=-obj["reserved_size"]
            )
            self.obj_repo.delete_object(obj["id"])
            count += 1
        return count
    
    def expand_reserved(self, obj_id: str, extra_bytes: int) -> bool:
        obj = self.obj_repo.get_object(obj_id)
        if obj is None:
            return False
        # Проверяем место прямо здесь
        disk = self.disk_repo.get_disk(obj["disk_id"])
        if disk is None:
            return False
        
        if disk["status"] not in ("available", "readonly"):   # только для записи
            return False
    
        free = disk["total_space"] - (disk["used_space"] + disk["reserved_space"])
        if free < extra_bytes:
            return False

        self.disk_repo.update_disk_space(obj["disk_id"], used_delta=0, reserved_delta=extra_bytes)
        new_reserved = obj["reserved_size"] + extra_bytes
        self.obj_repo.update_object(obj_id, reserved_size=new_reserved)
        return True
    
    def get_disk_info(self, disk_id: int) -> dict | None:
        return self.disk_repo.get_disk(disk_id)
    
    def get_all_disks(self) -> list[dict]:
        return self.disk_repo.get_all_disks()
    
    def set_object_size(self, obj_id: str, actual_size: int) -> None:
        obj = self.obj_repo.get_object(obj_id)
        if obj is None:
            raise ObjectNotFoundError(f"Объект {obj_id} не найден")
        
        # Запоминаем старый размер
        old_size = obj["current_size"]
        disk_id = obj["disk_id"]
        # Вычисляем изменение
        delta = actual_size - old_size        
        # Обновляем current_size у объекта
        self.obj_repo.update_object(obj_id, current_size=actual_size)
        # Корректируем used_space на диске
        self.disk_repo.update_disk_space(disk_id=disk_id, used_delta=delta, reserved_delta=0)