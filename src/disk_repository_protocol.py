from typing import Protocol

class DiskRepositoryProtocol(Protocol):
    def add_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        pass

    def get_disk(self, disk_id: int) -> dict | None:
        pass

    def get_all_disks(self) -> list[dict]:
        pass

    def update_disk_space(self, disk_id: int, used_delta: int, reserved_delta: int) -> None: #used_delta - изменение used_space, reserved_delta - изменение reserved_space
        pass

    def update_disk_status(self, disk_id: int, status: str) -> None:
        pass

    def close(self):
        pass