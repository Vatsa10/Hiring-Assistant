import sqlite3
import json
from models import CandidateInfo

class DatabaseManager:
    def __init__(self, db_path="hiring_assistant.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    years_of_experience REAL,
                    desired_positions TEXT,
                    current_location TEXT,
                    tech_stack TEXT,
                    technical_questions TEXT,
                    conversation_history TEXT,
                    is_complete BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_candidate(self, info_dict, history, is_complete):
        # Flatten lists for storage
        info = info_dict.copy()
        info['desired_positions'] = json.dumps(info.get('desired_positions', []))
        info['tech_stack'] = json.dumps(info.get('tech_stack', []))
        info['technical_questions'] = json.dumps(info.get('technical_questions', []))
        history_json = json.dumps(history)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Try to update if email exists, otherwise insert
            email = info.get('email')
            if email:
                cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("""
                        UPDATE candidates SET 
                            full_name = ?, phone = ?, years_of_experience = ?, 
                            desired_positions = ?, current_location = ?, tech_stack = ?, 
                            technical_questions = ?, conversation_history = ?, is_complete = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        info.get('full_name'), info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'],
                        info['technical_questions'], history_json, is_complete, row[0]
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO candidates (
                            full_name, email, phone, years_of_experience, 
                            desired_positions, current_location, tech_stack, 
                            technical_questions, conversation_history, is_complete
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        info.get('full_name'), email, info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'],
                        info['technical_questions'], history_json, is_complete
                    ))
            else:
                # No email, just insert as new entry (potential duplicates but avoids null email unique constraint issues)
                cursor.execute("""
                    INSERT INTO candidates (
                        full_name, email, phone, years_of_experience, 
                        desired_positions, current_location, tech_stack, 
                        technical_questions, conversation_history, is_complete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    info.get('full_name'), None, info.get('phone'), info.get('years_of_experience'),
                    info['desired_positions'], info.get('current_location'), info['tech_stack'],
                    info['technical_questions'], history_json, is_complete
                ))
            conn.commit()

    def get_candidate_by_email(self, email):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['desired_positions'] = json.loads(data['desired_positions'])
                data['tech_stack'] = json.loads(data['tech_stack'])
                data['technical_questions'] = json.loads(data['technical_questions'])
                history = json.loads(data['conversation_history'])
                return data, history
            return None, None
