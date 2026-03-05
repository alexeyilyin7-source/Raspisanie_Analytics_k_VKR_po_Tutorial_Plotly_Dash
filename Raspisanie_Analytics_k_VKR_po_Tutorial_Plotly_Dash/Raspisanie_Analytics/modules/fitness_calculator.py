# modules/fitness_calculator.py
import numpy as np
import pandas as pd


class FitnessCalculator:
    """Класс для расчета fitness-функции расписания"""

    def __init__(self):
        # Веса для мягких ограничений
        self.weights = {
            'windows_penalty': 0.3,  # Штраф за окна
            'load_imbalance': 0.25,  # Неравномерность нагрузки
            'preferences_violation': 0.25,  # Нарушение пожеланий
            'room_usage': 0.2  # Использование аудиторий
        }

    def calculate_windows_penalty(self, schedule_df):
        """Расчет штрафа за окна в расписании"""
        if schedule_df.empty or 'teacher_name' not in schedule_df.columns or 'date' not in schedule_df.columns:
            return 0

        penalty = 0
        for teacher in schedule_df['teacher_name'].unique():
            teacher_schedule = schedule_df[schedule_df['teacher_name'] == teacher]
            for date in teacher_schedule['date'].unique():
                day_classes = teacher_schedule[teacher_schedule['date'] == date]
                if len(day_classes) > 1:
                    # Чем больше разрывов, тем выше штраф
                    penalty += len(day_classes) * 0.5
        return penalty * self.weights['windows_penalty']

    def calculate_load_imbalance(self, schedule_df):
        """Расчет неравномерности нагрузки"""
        if schedule_df.empty or 'teacher_load' not in schedule_df.columns:
            return 0

        # Стандартное отклонение нагрузки
        load_std = schedule_df['teacher_load'].std() if len(schedule_df) > 1 else 0
        return load_std * self.weights['load_imbalance']

    def calculate_preferences_violation(self, schedule_df, teachers_df):
        """Расчет нарушений пожеланий преподавателей"""
        if schedule_df.empty or teachers_df is None or teachers_df.empty:
            return 0

        penalty = 0
        if 'teacher_name' not in schedule_df.columns:
            return penalty

        for _, row in schedule_df.iterrows():
            teacher_name = row.get('teacher_name')
            if teacher_name is None:
                continue

            teacher_data = teachers_df[teachers_df['full_name'] == teacher_name]

            if len(teacher_data) > 0:
                # Проверка на превышение максимальной нагрузки
                max_hours = teacher_data.iloc[0].get('max_hours_per_day', 4)
                if row.get('teacher_load', 0) > max_hours:
                    penalty += 2

                # Проверка предпочтений (упрощенно)
                preferences = teacher_data.iloc[0].get('preferences', '{}')
                if preferences != '{}' and pd.notna(preferences):
                    penalty += 1

        return penalty * self.weights['preferences_violation']

    def calculate_room_usage(self, schedule_df, classrooms_df):
        """Расчет эффективности использования аудиторий"""
        if schedule_df.empty or 'total_classes' not in schedule_df.columns:
            return 0

        # Чем больше занятий, тем лучше использование (меньше штраф)
        total_classes = schedule_df['total_classes'].sum()
        penalty = 100 / (total_classes + 1) if total_classes >= 0 else 100

        return penalty * self.weights['room_usage']

    def calculate_fitness(self, schedule_df, teachers_df=None, classrooms_df=None):
        """
        Расчет общей fitness-функции (чем меньше, тем лучше)
        Формула: F(X) = Σ(wi * Ci) → min
        """
        if schedule_df.empty:
            return {
                'total_penalty': 1000,
                'fitness': 0.001,
                'components': {
                    'windows': 0,
                    'load': 0,
                    'preferences': 0,
                    'room': 0
                }
            }

        total_penalty = 0
        windows_penalty = self.calculate_windows_penalty(schedule_df)
        load_penalty = self.calculate_load_imbalance(schedule_df)
        preferences_penalty = self.calculate_preferences_violation(schedule_df, teachers_df)
        room_penalty = self.calculate_room_usage(schedule_df, classrooms_df)

        total_penalty = windows_penalty + load_penalty + preferences_penalty + room_penalty

        # Fitness (чем выше, тем лучше особь)
        fitness = 1 / (1 + total_penalty) if total_penalty >= 0 else 0

        return {
            'total_penalty': total_penalty,
            'fitness': fitness,
            'components': {
                'windows': windows_penalty / self.weights['windows_penalty'] if self.weights[
                                                                                    'windows_penalty'] > 0 else 0,
                'load': load_penalty / self.weights['load_imbalance'] if self.weights['load_imbalance'] > 0 else 0,
                'preferences': preferences_penalty / self.weights['preferences_violation'] if self.weights[
                                                                                                  'preferences_violation'] > 0 else 0,
                'room': room_penalty / self.weights['room_usage'] if self.weights['room_usage'] > 0 else 0
            }
        }