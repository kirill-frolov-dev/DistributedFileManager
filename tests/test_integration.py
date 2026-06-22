import os
import tempfile
import time

import pytest

from src.exceptions import NotEnoughSpaceError
from src.sharding_manager import ShardingManager
from src.sqlite_disk_repository import SqliteDiskRepository
from src.sqlite_object_repository import SqliteObjectRepository


# Общая настройка для всех тестов
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

    shard_manager.set_object_size("obj_1", actual_size=200)

    disk = disk_repo.get_disk(disk_id)
    assert disk["used_space"] == 200
    assert disk["reserved_space"] == 300

    shard_manager.delete_object("obj_1")

    disk = disk_repo.get_disk(disk_id)
    assert disk["used_space"] == 0
    assert disk["reserved_space"] == 0

    obj = obj_repo.get_object("obj_1")
    assert obj is None

# Создание дисков с особыми статусами (один доступный и один недоступный)
def test_allocate_disk_skips_unavailable(manager):
    disk_repo, obj_repo, shard_manager = manager

    # Регистрируем два диска
    disk1 = shard_manager.register_disk("./disk1", total_space=1000, status="available")
    disk2 = shard_manager.register_disk("./disk2", total_space=1000, status="unavailable")

    # Ожидаем, что выберется только disk1
    disk_id = shard_manager.allocate_disk(500)
    assert disk_id == disk1

    # Проверяем, что disk2 не используется
    disk2_info = disk_repo.get_disk(disk2)
    assert disk2_info["reserved_space"] == 0

# Создание двух недоступных дисков
def test_allocate_disk_fails_when_no_disks_available(manager):
    disk_repo, obj_repo, shard_manager = manager

    # Регистрируем только недоступные диски
    shard_manager.register_disk("./disk1", total_space=1000, status="unavailable")
    shard_manager.register_disk("./disk2", total_space=1000, status="readonly")

    # Ожидаем исключение
    with pytest.raises(NotEnoughSpaceError, match="Нет подходящего диска с достаточным свободным местом"):
        shard_manager.allocate_disk(500)



# Очистка незавершённых объектов
def test_cleanup_stale(manager):
    disk_repo, obj_repo, shard_manager = manager

    disk_id = shard_manager.register_disk("./test_disk", total_space=1000)
    # Создаём объект и завершаем его
    shard_manager.create_object("obj_1", initial_size=300)
    shard_manager.complete_object("obj_1")
    # Создаём незавершённый объект
    shard_manager.create_object("obj_2", initial_size=200)

    # Ждём 2 секунды, чтобы created_at у объекта стал больше 1 секунды, и тогда cleanup_stale увидет объект и удалит его.
    time.sleep(2)
    count = shard_manager.cleanup_stale(older_than_seconds=1)
    assert count == 1

    # Проверяем чтобы завершённый объект остался
    completed = obj_repo.get_object("obj_1")
    assert completed is not None

    # Проверяем чтобы незавершённый объект был удалён
    stale = obj_repo.get_object("obj_2")
    assert stale is None
