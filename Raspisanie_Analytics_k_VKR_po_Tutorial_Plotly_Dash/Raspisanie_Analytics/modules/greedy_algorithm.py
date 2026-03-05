# modules/greedy_algorithm.py
import pandas as pd
import numpy as np
from modules.fitness_calculator import FitnessCalculator


class GreedyAlgorithm:
    """Жадный алгоритм для быстрого построения расписания"""

    def __init__(self):
        self.fitness_calculator = FitnessCalculator()

    def schedule_by_priority(self, base_data, teachers_df, classrooms_df,
                             priority='load'):
        """
        Построение расписания на основе приоритетов

        priority: 'load' - по нагрузке (сначала самые загруженные)
                 'classes' - по количеству занятий
                 'balanced' - сбалансированный подход
        """
        if base_data.empty:
            return base_data

        schedule = base_data.copy()

        if priority == 'load' and 'teacher_load' in schedule.columns:
            # Сортировка по убыванию нагрузки
            schedule = schedule.sort_values('teacher_load', ascending=False)

        elif priority == 'classes' and 'total_classes' in schedule.columns:
            # Сортировка по убыванию количества занятий
            schedule = schedule.sort_values('total_classes', ascending=False)

        elif priority == 'balanced':
            # Комбинированный подход
            if 'teacher_load' in schedule.columns and 'total_classes' in schedule.columns:
                # Нормализация значений
                schedule['load_norm'] = (schedule['teacher_load'] - schedule['teacher_load'].min()) / \
                                        (schedule['teacher_load'].max() - schedule['teacher_load'].min() + 1)
                schedule['classes_norm'] = (schedule['total_classes'] - schedule['total_classes'].min()) / \
                                           (schedule['total_classes'].max() - schedule['total_classes'].min() + 1)
                schedule['priority_score'] = schedule['load_norm'] * 0.6 + schedule['classes_norm'] * 0.4
                schedule = schedule.sort_values('priority_score', ascending=False)
                schedule = schedule.drop(['load_norm', 'classes_norm', 'priority_score'], axis=1)

        return schedule

    def distribute_evenly(self, base_data):
        """Равномерное распределение нагрузки по дням"""
        if base_data.empty or 'date' not in base_data.columns:
            return base_data

        # Группировка по датам и перераспределение
        date_groups = base_data.groupby('date')

        distributed = []
        for date, group in date_groups:
            if 'teacher_load' in group.columns:
                # Усреднение нагрузки в группе
                avg_load = group['teacher_load'].mean()
                group['teacher_load'] = avg_load
            distributed.append(group)

        return pd.concat(distributed) if distributed else base_data

    def run(self, base_data, teachers_df, classrooms_df,
            priority='balanced', distribute=True):
        """
        Запуск жадного алгоритма
        """
        print(f"🔄 Запуск жадного алгоритма:")
        print(f"   Приоритет: {priority}")
        print(f"   Равномерное распределение: {distribute}")

        if base_data.empty:
            print("   Нет данных для построения")
            return base_data

        # Построение по приоритетам
        result = self.schedule_by_priority(base_data, teachers_df,
                                           classrooms_df, priority)

        # Равномерное распределение
        if distribute:
            result = self.distribute_evenly(result)

        # Расчет fitness
        fitness_result = self.fitness_calculator.calculate_fitness(
            result, teachers_df, classrooms_df
        )

        print(f"✅ Жадный алгоритм завершен")
        print(f"   Fitness: {fitness_result['fitness']:.4f}")
        print(f"   Штраф: {fitness_result['total_penalty']:.2f}")

        return result