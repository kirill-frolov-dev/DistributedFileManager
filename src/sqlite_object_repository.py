from typing import List, Dict, Optional

class SqliteObjectRepository:
    def __init__(self, db_path: str):
        pass
    
    def _init_tables(self):
        pass

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