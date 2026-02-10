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
                    strongest_areas TEXT,
                    preferences TEXT,
                    technical_questions TEXT,
                    current_question_index INTEGER DEFAULT 0,
                    conversation_history TEXT,
                    is_complete BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Migration checks
            cursor.execute("PRAGMA table_info(candidates)")
            columns = [column[1] for column in cursor.fetchall()]
            migration_needed = False
            
            if 'preferences' not in columns:
                cursor.execute("ALTER TABLE candidates ADD COLUMN preferences TEXT")
                migration_needed = True
            if 'strongest_areas' not in columns:
                cursor.execute("ALTER TABLE candidates ADD COLUMN strongest_areas TEXT")
                migration_needed = True
            if 'current_question_index' not in columns:
                cursor.execute("ALTER TABLE candidates ADD COLUMN current_question_index INTEGER DEFAULT 0")
                migration_needed = True
            
            if migration_needed:
                conn.commit()

    def save_candidate(self, info_dict, history, is_complete):
        # Flatten lists for storage
        info = info_dict.copy()
        info['desired_positions'] = json.dumps(info.get('desired_positions', []))
        info['tech_stack'] = json.dumps(info.get('tech_stack', []))
        info['strongest_areas'] = json.dumps(info.get('strongest_areas', []))
        info['technical_questions'] = json.dumps(info.get('technical_questions', []))
        history_json = json.dumps(history)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            email = info.get('email')
            if email:
                cursor.execute("SELECT id FROM candidates WHERE email = ?", (email,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("""
                        UPDATE candidates SET 
                            full_name = ?, phone = ?, years_of_experience = ?, 
                            desired_positions = ?, current_location = ?, tech_stack = ?, 
                            strongest_areas = ?, preferences = ?, technical_questions = ?, 
                            current_question_index = ?, conversation_history = ?, is_complete = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        info.get('full_name'), info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'],
                        info['strongest_areas'], info.get('preferences'), info['technical_questions'], 
                        info.get('current_question_index', 0), history_json, is_complete, row[0]
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO candidates (
                            full_name, email, phone, years_of_experience, 
                            desired_positions, current_location, tech_stack, strongest_areas,
                            preferences, technical_questions, current_question_index, 
                            conversation_history, is_complete
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        info.get('full_name'), email, info.get('phone'), info.get('years_of_experience'),
                        info['desired_positions'], info.get('current_location'), info['tech_stack'], 
                        info['strongest_areas'], info.get('preferences'), info['technical_questions'], 
                        info.get('current_question_index', 0), history_json, is_complete
                    ))
            else:
                cursor.execute("""
                    INSERT INTO candidates (
                        full_name, email, phone, years_of_experience, 
                        desired_positions, current_location, tech_stack, strongest_areas,
                        preferences, technical_questions, current_question_index, 
                        conversation_history, is_complete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    info.get('full_name'), None, info.get('phone'), info.get('years_of_experience'),
                    info['desired_positions'], info.get('current_location'), info['tech_stack'], 
                    info['strongest_areas'], info.get('preferences'), info['technical_questions'], 
                    info.get('current_question_index', 0), history_json, is_complete
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
                data['strongest_areas'] = json.loads(data['strongest_areas'] or '[]')
                data['technical_questions'] = json.loads(data['technical_questions'] or '[]')
                history = json.loads(data['conversation_history'] or '[]')
                return data, history
            return None, None
