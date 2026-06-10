from typing import Protocol, List, Dict, Optional

class ObjectRepositoryProtocol(Protocol):
    def add_object(self, obj_id: str, disk_id: int, reserved_size: int) -> None:
        pass

    def get_object(self, obj_id: str) -> Optional[Dict] :
        pass

    def update_object(self, obj_id: str, **kwargs) -> bool:
        pass

    def delete_object(self, obj_id: str) -> bool:
        pass

    def get_incomplete_objects(self, older_than_seconds: int) -> List[Dict]:
        pass