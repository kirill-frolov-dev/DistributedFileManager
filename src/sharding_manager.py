from typing import Optional, List, Dict
from .disk_repository_protocol import DiskRepositoryProtocol
from .object_repository_protocol import ObjectRepositoryProtocol

class ShardingManager:
    def __init__(self, disk_repo: DiskRepositoryProtocol, obj_repo: ObjectRepositoryProtocol):
        self.disk_repo = disk_repo
        self.obj_repo = obj_repo

    def register_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        return self.disk_repo.add_disk(mount_point, total_space, status)

    def allocate_disk(self, required_bytes: int) -> int:
        disks=self.disk_repo.get_all_disks()
        for disk in disks:
            free = disk["total_space"] - (disk["used_space"] + disk["reserved_space"])
            if free >= required_bytes:
                return disk["id"]
        raise RuntimeError("Не достаточно места на диске")
    def reserve_space(self, disk_id: int, bytes_to_reserve: int) -> None:
        self.disk_repo.update_disk_space(disk_id, used_delta=0, reserved_delta=bytes_to_reserve)

    def release_space(self, disk_id: int, used_bytes: int, reserved_bytes: int) -> None:
        pass

    def create_object(self, obj_id: str, initial_size: int) -> None:
        disk_id = self.allocate_disk(initial_size)
        self.reserve_space(disk_id, initial_size)
        self.obj_repo.add_object(obj_id, disk_id, initial_size)

    def complete_object(self, obj_id: str) -> None:
        pass

    def delete_object(self, obj_id: str) -> None:
        pass

    def cleanup_stale(self, older_than_seconds: int) -> int:
        pass
    def expand_reserved(self, obj_id: str, extra_bytes: int) -> bool:
        pass
    def get_disk_info(self, disk_id: int) -> Optional[Dict]:
        pass
    def get_all_disks(self) -> List[Dict]:
        pass