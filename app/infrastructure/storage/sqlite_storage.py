import json
from typing import Dict
from infrastructure.storage.base import ContextStorage

# Implementação de armazenamento com SQLite
class SQLiteStorage(ContextStorage):
    def __init__(self, db_path: str):
        try:
            import sqlite3
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_table()
        except ImportError:
            raise ImportError("SQLite3 não está disponível")
    
    def _create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS contexts (
            session_id TEXT PRIMARY KEY,
            context TEXT NOT NULL
        )
        """)
        self.conn.commit()
    
    def get(self, session_id: str) -> Dict:
        self.cursor.execute("SELECT context FROM contexts WHERE session_id = ?", (session_id,))
        result = self.cursor.fetchone()
        if result:
            return json.loads(result[0])
        return {}
    
    def set(self, session_id: str, context: Dict) -> None:
        context_json = json.dumps(context)
        self.cursor.execute("""
        INSERT OR REPLACE INTO contexts (session_id, context) VALUES (?, ?)
        """, (session_id, context_json))
        self.conn.commit()
    
    def delete(self, session_id: str) -> None:
        self.cursor.execute("DELETE FROM contexts WHERE session_id = ?", (session_id,))
        self.conn.commit()
    
    def exists(self, session_id: str) -> bool:
        self.cursor.execute("SELECT 1 FROM contexts WHERE session_id = ?", (session_id,))
        return bool(self.cursor.fetchone())