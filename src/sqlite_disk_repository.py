import sqlite3

class SqliteDiskRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS disks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mount_point TEXT NOT NULL,
                    total_space INTEGER NOT NULL,
                    used_space INTEGER NOT NULL DEFAULT 0,
                    reserved_space INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'available'
                    )''') 
        self.conn.commit()

    def add_disk(self, mount_point: str, total_space: int, status: str = "available") -> int:
        cur = self.conn.cursor()
        cur.execute('''INSERT INTO disks (mount_point, total_space, used_space, reserved_space, status) VALUES (?, ?, ?, ?, ?)''', (mount_point, total_space, 0, 0, status))
        self.conn.commit()
        return cur.lastrowid

    def get_disk(self, disk_id: int) -> dict | None:
        cur = self.conn.cursor()
        cur.execute('''SELECT * 
                    FROM disks 
                    WHERE id = ?''', [disk_id])
        row = cur.fetchone()
        return dict(row) if row else None

    def get_all_disks(self) -> list[dict]:
        cur = self.conn.cursor()
        cur.execute('''SELECT * 
                    FROM disks''')
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def update_disk_space(self, disk_id: int, used_delta: int, reserved_delta: int) -> None: #used_delta - изменение used_space, reserved_delta - изменение reserved_space
        cur = self.conn.cursor()
        cur.execute('''UPDATE disks 
                    SET used_space = used_space + ?, reserved_space = reserved_space + ? 
                    WHERE id = ?''', [used_delta, reserved_delta, disk_id])
        self.conn.commit()

    def update_disk_status(self, disk_id: int, status: str) -> None:
        cur = self.conn.cursor()
        cur.execute('''UPDATE disks 
                    SET status = ?
                    WHERE id = ?''', [status, disk_id])
        self.conn.commit()

    def close(self):
        self.conn.close()