# modules/database.py
import sqlite3
import pandas as pd
import os
from datetime import datetime


class DatabaseManager:
    """Класс для работы с базой данных (SQLite для прототипа)"""

    def __init__(self, db_path='schedule.db'):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Подключение к БД"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def disconnect(self):
        """Отключение от БД"""
        if self.conn:
            self.conn.close()

    def init_database(self):
        """Инициализация структуры БД"""
        conn = self.connect()
        cursor = conn.cursor()

        # Таблица институтов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS institutes (
                institute_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                abbreviation TEXT
            )
        ''')

        # Таблица кафедр
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                department_id TEXT PRIMARY KEY,
                institute_id TEXT,
                name TEXT NOT NULL,
                head_name TEXT,
                FOREIGN KEY (institute_id) REFERENCES institutes(institute_id)
            )
        ''')

        # Таблица преподавателей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                department_id TEXT,
                max_hours_per_day INTEGER,
                email TEXT,
                phone TEXT,
                preferences TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            )
        ''')

        # Таблица групп
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                institute_id TEXT,
                course INTEGER,
                student_count INTEGER,
                level TEXT,
                FOREIGN KEY (institute_id) REFERENCES institutes(institute_id)
            )
        ''')

        # Таблица дисциплин
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disciplines (
                discipline_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT
            )
        ''')

        # Таблица аудиторий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classrooms (
                classroom_id TEXT PRIMARY KEY,
                building TEXT,
                room_number TEXT,
                capacity INTEGER,
                room_type TEXT,
                equipment TEXT
            )
        ''')

        # Таблица учебных планов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curriculum (
                curriculum_id TEXT PRIMARY KEY,
                group_id TEXT,
                discipline_id TEXT,
                teacher_id TEXT,
                hours_per_semester INTEGER,
                semester TEXT,
                lesson_type TEXT,
                weeks_parity TEXT,
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (discipline_id) REFERENCES disciplines(discipline_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
            )
        ''')

        # Таблица расписания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                curriculum_id TEXT,
                classroom_id TEXT,
                date DATE,
                time_slot TEXT,
                is_cancelled BOOLEAN DEFAULT 0,
                cancel_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (curriculum_id) REFERENCES curriculum(curriculum_id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(classroom_id)
            )
        ''')

        conn.commit()
        print("✅ База данных инициализирована")

    def import_from_csv(self, data_loader):
        """Импорт данных из CSV в БД"""
        conn = self.connect()

        # Импорт институтов (уникальные из schedule_data)
        institutes = data_loader.schedule_data['institute'].unique()
        for inst in institutes:
            conn.execute(
                "INSERT OR IGNORE INTO institutes (institute_id, name) VALUES (?, ?)",
                (inst, inst)
            )

        # Импорт преподавателей
        if data_loader.teachers_data is not None:
            data_loader.teachers_data.to_sql('teachers', conn,
                                             if_exists='replace', index=False)

        # Импорт групп
        if data_loader.groups_data is not None:
            data_loader.groups_data.to_sql('groups', conn,
                                           if_exists='replace', index=False)

        # Импорт аудиторий
        if data_loader.classrooms_data is not None:
            data_loader.classrooms_data.to_sql('classrooms', conn,
                                               if_exists='replace', index=False)

        # Импорт учебных планов
        if data_loader.curriculum_data is not None:
            data_loader.curriculum_data.to_sql('curriculum', conn,
                                               if_exists='replace', index=False)

        conn.commit()
        print("✅ Данные импортированы в БД")

    def save_schedule(self, schedule_df, version_name=None):
        """Сохранение расписания в БД"""
        conn = self.connect()

        if version_name is None:
            version_name = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Сохраняем как CSV для простоты (в реальности - отдельная таблица)
        schedule_df.to_csv(f"data/{version_name}.csv", index=False)

        print(f"✅ Расписание сохранено как {version_name}.csv")
        return version_name

    def load_schedule(self, version_name):
        """Загрузка расписания из файла"""
        try:
            df = pd.read_csv(f"data/{version_name}.csv")
            print(f"✅ Расписание {version_name} загружено")
            return df
        except FileNotFoundError:
            print(f"❌ Файл {version_name}.csv не найден")
            return None


# Глобальный экземпляр
db_manager = DatabaseManager()