import sqlite3

class SqliteObjectRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS objects (
                    id TEXT PRIMARY KEY,
                    disk_id INTEGER NOT NULL,
                    current_size INTEGER NOT NULL DEFAULT 0,
                    reserved_size INTEGER NOT NULL DEFAULT 0,
                    readonly INTEGER NOT NULL DEFAULT 0,
                    is_completed INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (disk_id) REFERENCES disks(id) ON DELETE CASCADE
                    )''')
        self.conn.commit()

    def add_object(self, obj_id: str, disk_id: int, reserved_size: int) -> None:
        cur = self.conn.cursor()
        cur.execute('''INSERT INTO objects (id, disk_id, reserved_size) VALUES (?, ?, ?)''', (obj_id, disk_id, reserved_size))
        self.conn.commit()

    def get_object(self, obj_id: str) -> dict | None:
        cur = self.conn.cursor()
        cur.execute('''SELECT * 
                    FROM objects 
                    WHERE id = ?''', [obj_id])
        row = cur.fetchone()
        return dict(row) if row else None

    def update_object(self, obj_id: str, **kwargs) -> bool:
        if not kwargs: return False 
        fields = kwargs.keys()
        set_clause = ", ".join([f"{field} = ?" for field in fields])
        query = f"UPDATE objects SET {set_clause} WHERE id = ?"
        values = list(kwargs.values())
        values.append(obj_id)
        cursor = self.conn.execute(query, values)
        self.conn.commit()
        return cursor.rowcount > 0
        

    def delete_object(self, obj_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute('''DELETE FROM objects WHERE id=?''', [obj_id])
        self.conn.commit()
        return cur.rowcount > 0

    def get_incomplete_objects(self, older_than_seconds: int) -> list[dict]:
        cur = self.conn.cursor()
        rows = cur.execute('''SELECT * 
                    FROM objects 
                    WHERE is_completed = 0 AND created_at < datetime('now', ?)''', [f"-{older_than_seconds} seconds"]).fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        self.conn.close()