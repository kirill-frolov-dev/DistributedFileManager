import os
import tempfile
import pytest

from src.storage_library import StorageLibrary


@pytest.fixture
def storage():
    """Фикстура для StorageLibrary"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        lib = StorageLibrary(db_path)
        yield lib
        lib.close()


def test_register_disk_through_storage(storage):
    """Проверяет, что через StorageLibrary можно зарегистрировать диск"""
    disk_id = storage.register_disk("./test_disk", total_space=1000)
    assert disk_id is not None
    
    info = storage.get_disk_info(disk_id)
    assert info is not None
    assert info["total_space"] == 1000
    assert info["used_space"] == 0
    assert info["reserved_space"] == 0


def test_create_object_through_storage(storage):
    """Проверяет создание объекта через StorageLibrary"""
    storage.register_disk("./test_disk", total_space=1000)
    
    obj_id = storage.create_object(initial_size=300)
    assert obj_id is not None


def test_complete_object_through_storage(storage):
    """Проверяет завершение объекта через StorageLibrary"""
    disk_id = storage.register_disk("./test_disk", total_space=1000)
    obj_id = storage.create_object(initial_size=300)
    
    info = storage.get_disk_info(disk_id)
    assert info["reserved_space"] == 300
    
    storage.complete_object(obj_id)
    
    info = storage.get_disk_info(disk_id)
    assert info["reserved_space"] == 0


def test_delete_object_through_storage(storage):
    """Проверяет удаление объекта через StorageLibrary"""
    disk_id = storage.register_disk("./test_disk", total_space=1000)
    obj_id = storage.create_object(initial_size=300)
    
    storage.set_object_size(obj_id, actual_size=200)
    
    info = storage.get_disk_info(disk_id)
    assert info["used_space"] == 200
    assert info["reserved_space"] == 300
    
    storage.delete_object(obj_id)
    
    info = storage.get_disk_info(disk_id)
    assert info["used_space"] == 0
    assert info["reserved_space"] == 0


def test_expand_reserved_through_storage(storage):
    """Проверяет расширение резерва через StorageLibrary"""
    disk_id = storage.register_disk("./test_disk", total_space=1000)
    obj_id = storage.create_object(initial_size=300)
    
    result = storage.expand_reserved(obj_id, extra_bytes=200)
    assert result == True
    
    info = storage.get_disk_info(disk_id)
    assert info["reserved_space"] == 500


def test_get_all_disks_through_storage(storage):
    """Проверяет получение всех дисков через StorageLibrary"""
    storage.register_disk("./disk1", total_space=1000)
    storage.register_disk("./disk2", total_space=2000)
    storage.register_disk("./disk3", total_space=3000)
    
    disks = storage.get_all_disks()
    assert len(disks) == 3
    assert disks[0]["total_space"] == 1000
    assert disks[1]["total_space"] == 2000
    assert disks[2]["total_space"] == 3000


def test_update_disk_status_through_storage(storage):
    """Проверяет обновление статуса диска через StorageLibrary"""
    disk_id = storage.register_disk("./test_disk", total_space=1000, status="available")
    
    storage.update_disk_status(disk_id, "readonly")
    info = storage.get_disk_info(disk_id)
    assert info["status"] == "readonly"
    
    storage.update_disk_status(disk_id, "unavailable")
    info = storage.get_disk_info(disk_id)
    assert info["status"] == "unavailable"


def test_cleanup_stale_through_storage(storage):
    """Проверяет очистку stale-объектов через StorageLibrary"""
    import time
    
    storage.register_disk("./test_disk", total_space=1000)
    
    # Создаём завершённый объект
    storage.create_object(obj_id="completed", initial_size=300)
    storage.complete_object("completed")
    
    # Создаём незавершённый объект
    storage.create_object(obj_id="stale", initial_size=200)
    
    time.sleep(2)
    count = storage.cleanup_stale(older_than_seconds=1)
    assert count == 1