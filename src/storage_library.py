from typing import Optional

class StorageLibrary:
    def __init__(self, db_path: str) -> None:
        pass
    
    def register_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        pass
    
    def create_object(self, obj_id: str, initial_size: int) -> None:
        pass
    
    def expand_reserved(self, obj_id: str, extra_bytes: int) -> bool:
        pass
    
    def delete_object(self, obj_id: str) -> None:
        pass
    
    def get_object_path(self, obj_id: str) -> Optional[str]:
        pass
    
    def cleanup_stale(self, older_than_seconds: int) -> int:
        pass
    
    def close(self) -> None:
        pass