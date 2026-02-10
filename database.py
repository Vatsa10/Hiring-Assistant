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
                    current_question_index INTEGER DEFAULT 0,
                    conversation_history TEXT,
                    is_complete BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Check if current_question_index column exists (for migration)
            cursor.execute("PRAGMA table_info(candidates)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'current_question_index' not in columns:
                cursor.execute("ALTER TABLE candidates ADD COLUMN current_question_index INTEGER DEFAULT 0")
            
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
                            technical_questions = ?, current_question_index = ?, 
                            conversation_history = ?, is_complete = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        info.get('full_name'), info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'],
                        info['technical_questions'], info.get('current_question_index', 0),
                        history_json, is_complete, row[0]
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO candidates (
                            full_name, email, phone, years_of_experience, 
                            desired_positions, current_location, tech_stack, 
                            technical_questions, current_question_index, conversation_history, is_complete
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        info.get('full_name'), email, info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'],
                        info['technical_questions'], info.get('current_question_index', 0), history_json, is_complete
                    ))
            else:
                cursor.execute("""
                    INSERT INTO candidates (
                        full_name, email, phone, years_of_experience, 
                        desired_positions, current_location, tech_stack, 
                        technical_questions, current_question_index, conversation_history, is_complete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    info.get('full_name'), None, info.get('phone'), info.get('years_of_experience'),
                    info['desired_positions'], info.get('current_location'), info['tech_stack'],
                    info['technical_questions'], info.get('current_question_index', 0), history_json, is_complete
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
                data['desired_positions'] = json.loads(data['desired_positions'] or '[]')
                data['tech_stack'] = json.loads(data['tech_stack'] or '[]')
                data['technical_questions'] = json.loads(data['technical_questions'] or '[]')
                history = json.loads(data['conversation_history'] or '[]')
                return data, history
            return None, None
