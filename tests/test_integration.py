import tempfile
import os
import pytest
from src.sharding_manager import ShardingManager
from src.sqlite_disk_repository import SqliteDiskRepository
from src.sqlite_object_repository import SqliteObjectRepository

#Общая настройка для всех тестов
@pytest.fixture
def manager():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        disk_repo = SqliteDiskRepository(db_path)
        obj_repo = SqliteObjectRepository(db_path)
        shard_manager = ShardingManager(disk_repo, obj_repo)

        yield disk_repo, obj_repo, shard_manager

        disk_repo.close()
        obj_repo.close()

# Регистрация диска, начальные значения
def test_register_disk(manager):
    disk_repo, obj_repo, shard_manager = manager
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    disk = disk_repo.get_disk(disk_id)
    assert disk is not None
    assert disk["total_space"] == 1000
    assert disk["used_space"] == 0
    assert disk["reserved_space"] == 0

# Создание объекта и резервирование места
def test_create_object_reserves_space(manager):
    disk_repo, obj_repo, shard_manager = manager
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    shard_manager.create_object("obj_1", initial_size=300)

    disk = disk_repo.get_disk(disk_id)
    assert disk["used_space"] == 0
    assert disk["reserved_space"] == 300
    
    obj = obj_repo.get_object("obj_1")
    assert obj is not None
    assert obj["current_size"] == 0
    assert obj["reserved_size"] == 300
    assert obj["is_completed"] == 0
    assert obj["disk_id"] == disk_id


# Завершение объекта, освобождение резерва
def test_complete_object_releases_space(manager):
    disk_repo, obj_repo, shard_manager = manager

    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    shard_manager.create_object("obj_1", initial_size=300)

    disk = disk_repo.get_disk(disk_id)
    assert disk["reserved_space"] == 300

    shard_manager.complete_object("obj_1")

    disk = disk_repo.get_disk(disk_id)
    assert disk["reserved_space"] == 0
    assert disk["used_space"] == 300

    obj = obj_repo.get_object("obj_1")
    assert obj["is_completed"] == 1
    assert obj["reserved_size"] == 0


# Проверка возможности расширение резерва
def test_expand_reserved(manager):
    disk_repo, obj_repo, shard_manager = manager
    
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    shard_manager.create_object("obj_1", initial_size=300)

    result = shard_manager.expand_reserved("obj_1", extra_bytes=200)
    assert result == True

    obj = obj_repo.get_object("obj_1")
    assert obj["reserved_size"] == 500
    
    disk = disk_repo.get_disk(disk_id)
    assert disk["reserved_space"] == 500


# Отказ расширения при нехватке места
def test_expand_reserved_fails_when_no_space(manager):
    disk_repo, obj_repo, shard_manager = manager
    
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    shard_manager.create_object("obj_1", initial_size=900)
    
    # Пытаемся расширить на 200 байт, а свободно только 100
    result = shard_manager.expand_reserved("obj_1", extra_bytes=200)
    assert result == False
    
    obj = obj_repo.get_object("obj_1")
    assert obj["reserved_size"] == 900 


# Удаление объекта, освобождение всего места
def test_delete_object(manager):
    disk_repo, obj_repo, shard_manager = manager
    
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    shard_manager.create_object("obj_1", initial_size=300)

    obj_repo.update_object("obj_1", current_size=200)
    disk_repo.update_disk_space(disk_id, used_delta=200, reserved_delta=0)

    disk = disk_repo.get_disk(disk_id)
    assert disk["used_space"] == 200
    assert disk["reserved_space"] == 300

    shard_manager.delete_object("obj_1")
    
    disk = disk_repo.get_disk(disk_id)
    assert disk["used_space"] == 0
    assert disk["reserved_space"] == 0

    obj = obj_repo.get_object("obj_1")
    assert obj is None


# Очистка незавершённых объектов
def test_cleanup_stale(manager):
    disk_repo, obj_repo, shard_manager = manager
    
    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    # Создаём объект и завершаем его
    shard_manager.create_object("obj_1", initial_size=300)
    shard_manager.complete_object("obj_1")
    # Создаём незавершённый объект
    shard_manager.create_object("obj_2", initial_size=200)

    count = shard_manager.cleanup_stale(older_than_seconds=0)
    assert count == 1

    # Проверяем чтобы завершённый объект остался
    completed = obj_repo.get_object("completed_obj")
    assert completed is not None

    # Проверяем чтобы незавершённый объект был удалён
    stale = obj_repo.get_object("stale_obj")
    assert stale is None