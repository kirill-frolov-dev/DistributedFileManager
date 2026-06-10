from typing import Optional
from .disk_repository_protocol import DiskRepositoryProtocol
from .object_repository_protocol import ObjectRepositoryProtocol

class ShardingManager:
    def __init__(self, disk_repo: DiskRepositoryProtocol, obj_repo: ObjectRepositoryProtocol):
        pass

    def register_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        pass

    def allocate_disk(self, required_bytes: int) -> int:
        pass

    def reserve_space(self, disk_id: int, bytes_to_reserve: int) -> None:
        pass

    def release_space(self, disk_id: int, used_bytes: int, reserved_bytes: int) -> None:
        pass

    def expand_reserved(self, disk_id, extra_bytes): #extra_bytes - на сколько байт нужно увеличить reserved_space
        pass

    def complete_object(self, obj_id: str) -> None:
        pass

    def delete_object(self, obj_id: str) -> None:
        pass

    def get_object_location(self, obj_id: str) -> Optional[str]:
        pass

    def cleanup_stale(self, older_than_seconds: int) -> int:
        pass

    