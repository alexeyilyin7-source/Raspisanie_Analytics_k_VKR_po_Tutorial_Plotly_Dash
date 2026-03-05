# modules/schedule_validator.py
import pandas as pd
import numpy as np


class ScheduleValidator:
    """Класс для проверки соблюдения ограничений в расписании"""

    def __init__(self):
        self.hard_constraints_violations = []
        self.soft_constraints_violations = []

    def check_hard_constraints(self, schedule_df, teachers_df,
                               groups_df, classrooms_df):
        """
        Проверка жестких ограничений (должны выполняться всегда)
        Возвращает (is_valid, list_of_violations)
        """
        violations = []

        # 1. Один преподаватель не может вести два занятия одновременно
        if 'teacher_name' in schedule_df.columns and 'date' in schedule_df.columns:
            teacher_date_counts = schedule_df.groupby(['teacher_name', 'date']).size()
            conflicts = teacher_date_counts[teacher_date_counts > 1]
            for (teacher, date), count in conflicts.items():
                violations.append({
                    'type': 'teacher_overlap',
                    'teacher': teacher,
                    'date': date,
                    'count': count,
                    'message': f"Преподаватель {teacher} имеет {count} занятий {date}"
                })

        # 2. Одна группа не может быть в двух местах одновременно
        if 'group_name' in schedule_df.columns and 'date' in schedule_df.columns:
            group_date_counts = schedule_df.groupby(['group_name', 'date']).size()
            conflicts = group_date_counts[group_date_counts > 1]
            for (group, date), count in conflicts.items():
                violations.append({
                    'type': 'group_overlap',
                    'group': group,
                    'date': date,
                    'count': count,
                    'message': f"Группа {group} имеет {count} занятий {date}"
                })

        # 3. Проверка вместимости аудиторий
        if classrooms_df is not None and 'group_name' in schedule_df.columns:
            for _, row in schedule_df.iterrows():
                group_name = row.get('group_name')
                group_data = groups_df[groups_df['group_name'] == group_name] if groups_df is not None else None

                if group_data is not None and len(group_data) > 0:
                    student_count = group_data.iloc[0].get('student_count', 30)
                    # В демо-режиме используем среднюю аудиторию 50
                    if student_count > 50:
                        violations.append({
                            'type': 'capacity',
                            'group': group_name,
                            'students': student_count,
                            'message': f"Группа {group_name} ({student_count} чел.) может превышать вместимость"
                        })

        # 4. Проверка превышения максимальной нагрузки преподавателя
        if teachers_df is not None and 'teacher_name' in schedule_df.columns:
            for _, row in schedule_df.iterrows():
                teacher_name = row.get('teacher_name')
                teacher_load = row.get('teacher_load', 0)
                teacher_data = teachers_df[teachers_df['full_name'] == teacher_name]

                if len(teacher_data) > 0:
                    max_load = teacher_data.iloc[0].get('max_hours_per_day', 4)
                    if teacher_load > max_load:
                        violations.append({
                            'type': 'teacher_overload',
                            'teacher': teacher_name,
                            'load': teacher_load,
                            'max': max_load,
                            'message': f"Преподаватель {teacher_name}: нагрузка {teacher_load} > {max_load}"
                        })

        self.hard_constraints_violations = violations
        is_valid = len(violations) == 0

        return is_valid, violations

    def check_soft_constraints(self, schedule_df, teachers_df):
        """
        Проверка мягких ограничений (желательные, но не обязательные)
        Возвращает список нарушений с весами
        """
        violations = []

        # 1. Проверка пожеланий преподавателей
        if teachers_df is not None and 'teacher_name' in schedule_df.columns:
            for _, row in schedule_df.iterrows():
                teacher_name = row.get('teacher_name')
                teacher_data = teachers_df[teachers_df['full_name'] == teacher_name]

                if len(teacher_data) > 0:
                    preferences = teacher_data.iloc[0].get('preferences', '{}')
                    # Упрощенная проверка
                    if 'avoid' in str(preferences).lower():
                        violations.append({
                            'type': 'preference',
                            'teacher': teacher_name,
                            'weight': 0.5,
                            'message': f"Пожелания преподавателя {teacher_name} могут быть нарушены"
                        })

        # 2. Проверка на "окна" (упрощенно)
        if 'teacher_name' in schedule_df.columns and 'date' in schedule_df.columns:
            for teacher in schedule_df['teacher_name'].unique():
                teacher_dates = schedule_df[schedule_df['teacher_name'] == teacher]['date'].nunique()
                if teacher_dates > 5:  # Больше 5 разных дней
                    violations.append({
                        'type': 'windows',
                        'teacher': teacher,
                        'weight': 0.3,
                        'message': f"Возможны окна в расписании преподавателя {teacher}"
                    })

        self.soft_constraints_violations = violations
        return violations

    def get_validation_report(self):
        """Получение отчета по валидации"""
        report = {
            'hard_constraints': {
                'count': len(self.hard_constraints_violations),
                'violations': self.hard_constraints_violations
            },
            'soft_constraints': {
                'count': len(self.soft_constraints_violations),
                'violations': self.soft_constraints_violations
            }
        }
        return report