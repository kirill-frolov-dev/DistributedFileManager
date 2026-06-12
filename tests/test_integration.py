import tempfile
import os
from src.sharding_manager import ShardingManager
from src.sqlite_disk_repository import SqliteDiskRepository
from src.sqlite_object_repository import SqliteObjectRepository

def test_create_object_reserves_space():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")

        disk_repo = SqliteDiskRepository(db_path)
        obj_repo = SqliteObjectRepository(db_path)
        manager = ShardingManager(disk_repo, obj_repo)

        disk_id = manager.register_disk("./test_disk", total_space=1000)
        manager.create_object("obj_1", initial_size=300)

        disk = disk_repo.get_disk(disk_id)
        assert disk["used_space"] == 0
        assert disk["reserved_space"] == 300

        obj = obj_repo.get_object("obj_1")
        assert obj is not None
        assert obj["current_size"] == 0
        assert obj["reserved_size"] == 300
        assert obj["is_completed"] == 0
        assert obj["disk_id"] == disk_id

        disk_repo.close()
        obj_repo.close()
