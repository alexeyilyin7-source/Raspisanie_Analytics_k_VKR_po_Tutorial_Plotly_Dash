# modules/data_loader.py
import pandas as pd
import numpy as np
import os
from datetime import datetime


class DataLoader:
    """Класс для загрузки и валидации всех данных системы"""

    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.schedule_data = None
        self.teachers_data = None
        self.groups_data = None
        self.classrooms_data = None
        self.curriculum_data = None

    def load_all_data(self):
        """Загрузка всех данных из CSV файлов"""
        try:
            self.schedule_data = pd.read_csv(os.path.join(self.data_path, 'schedule_data.csv'))
            self.teachers_data = pd.read_csv(os.path.join(self.data_path, 'teachers.csv'))
            self.groups_data = pd.read_csv(os.path.join(self.data_path, 'groups.csv'))
            self.classrooms_data = pd.read_csv(os.path.join(self.data_path, 'classrooms.csv'))
            self.curriculum_data = pd.read_csv(os.path.join(self.data_path, 'curriculum.csv'))

            # Предобработка данных
            self._preprocess_data()

            print("✅ Все данные успешно загружены")
            return True

        except FileNotFoundError as e:
            print(f"❌ Ошибка загрузки: {e}")
            print("Генерация демонстрационных данных...")
            self._generate_mock_data()
            return True
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")
            return False

    def _preprocess_data(self):
        """Предобработка данных"""
        if self.schedule_data is not None:
            self.schedule_data['date'] = pd.to_datetime(self.schedule_data['date'])
            self.schedule_data.sort_values('date', inplace=True)

    def _generate_mock_data(self):
        """Генерация демонстрационных данных"""
        dates = pd.date_range(start='2025-09-01', end='2025-12-31', freq='W')
        institutes = ['ИИС', 'ИОМ', 'ИЭФ', 'ИУПСиБК', 'ИМ', 'ИГУиП', 'ИЗО']
        lesson_types = ['Лекция', 'Семинар', 'Лабораторная']

        # Генерация schedule_data
        data = []
        teachers_list = []
        groups_list = []

        for i, institute in enumerate(institutes):
            for j, date in enumerate(dates[:10]):  # Первые 10 недель
                for lesson_type in lesson_types:
                    # Основные данные расписания
                    data.append({
                        'institute': institute,
                        'lesson_type': lesson_type,
                        'date': date,
                        'teacher_load': round(np.random.uniform(1.5, 4.5), 1),
                        'total_classes': np.random.randint(5, 15),
                        'teacher_name': f"Преподаватель {chr(65 + i)}{j}",
                        'group_name': f"{institute}-{j % 3 + 1}",
                        'discipline': f"Дисциплина {j + 1}"
                    })

                    # Данные преподавателей (уникальные)
                    if len(teachers_list) < 20:
                        teachers_list.append({
                            'teacher_id': f"T{len(teachers_list) + 1:03d}",
                            'full_name': f"Преподаватель {chr(65 + i)}{j}",
                            'department': institute,
                            'max_hours_per_day': np.random.choice([3, 4]),
                            'email': f"teacher{len(teachers_list) + 1}@guu.ru",
                            'phone': f"+7(495){np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(10, 99)}",
                            'preferences': '{}'
                        })

                    # Данные групп (уникальные)
                    group_name = f"{institute}-{j % 4 + 1}"
                    if group_name not in [g['group_name'] for g in groups_list]:
                        groups_list.append({
                            'group_id': f"G{len(groups_list) + 1:03d}",
                            'group_name': group_name,
                            'institute': institute,
                            'course': j % 4 + 1,
                            'student_count': np.random.randint(15, 35),
                            'level': np.random.choice(['Бакалавр', 'Магистр', 'Аспирант'])
                        })

        self.schedule_data = pd.DataFrame(data)
        self.teachers_data = pd.DataFrame(teachers_list)
        self.groups_data = pd.DataFrame(groups_list)

        # Генерация аудиторий
        classrooms = []
        buildings = ['Главный корпус', 'Учебный корпус 2', 'Лабораторный корпус']
        room_types = ['ЛК', 'ПА', 'А', 'ЦИТ', 'ГУ', 'ЦУВП']

        for i in range(15):
            classrooms.append({
                'room_id': f"R{i + 1:03d}",
                'building': np.random.choice(buildings),
                'room_number': str(100 + i),
                'capacity': np.random.choice([20, 30, 40, 50, 80, 100]),
                'room_type': np.random.choice(room_types),
                'equipment': 'Стандартное оснащение'
            })
        self.classrooms_data = pd.DataFrame(classrooms)

        # Генерация учебных планов
        curriculum = []
        for i in range(20):
            curriculum.append({
                'plan_id': f"P{i + 1:03d}",
                'group_id': np.random.choice(groups_list)['group_id'],
                'discipline': f"Дисциплина {i + 1}",
                'teacher_id': np.random.choice(teachers_list)['teacher_id'],
                'hours_per_semester': np.random.choice([36, 72, 108]),
                'semester': np.random.choice(['Осенний-Зимний', 'Весенний']),
                'lesson_type': np.random.choice(lesson_types),
                'weeks_parity': np.random.choice(['Оба', 'Четные', 'Нечетные'])
            })
        self.curriculum_data = pd.DataFrame(curriculum)

        print("✅ Демонстрационные данные сгенерированы")

    def get_filtered_data(self, institute=None, lesson_type=None,
                          start_date=None, end_date=None):
        """Получение отфильтрованных данных"""
        data = self.schedule_data.copy()

        if institute and institute != 'Все':
            data = data[data['institute'] == institute]
        if lesson_type and lesson_type != 'Все':
            data = data[data['lesson_type'] == lesson_type]
        if start_date:
            data = data[data['date'] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data['date'] <= pd.to_datetime(end_date)]

        return data


# Глобальный экземпляр для использования в приложении
loader = DataLoader()
loader.load_all_data()