class StorageError(Exception):
    #Базовое исключение для всех ошибок библиотеки
    pass


class DiskNotFoundError(StorageError):
    #Диск не найден
    pass


class NotEnoughSpaceError(StorageError):
    #Недостаточно свободного места на диске
    pass


class DiskUnavailableError(StorageError):
    #Диск недоступен (статус не 'available')
    pass


class ObjectNotFoundError(StorageError):
    #Объект не найден
    pass


class ObjectAlreadyExistsError(StorageError):
    #Объект с таким ID уже существует
    pass
