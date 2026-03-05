# modules/simulated_annealing.py
import numpy as np
import random
import math
from modules.fitness_calculator import FitnessCalculator


class SimulatedAnnealing:
    """Алгоритм имитации отжига для улучшения расписания"""

    def __init__(self, initial_temperature=100.0, cooling_rate=0.95,
                 min_temperature=0.1, max_iterations=1000):
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.max_iterations = max_iterations
        self.fitness_calculator = FitnessCalculator()
        self.temperature_history = []
        self.fitness_history = []

    def generate_neighbor(self, solution, teachers_df, classrooms_df):
        """Генерация соседнего решения (мутация)"""
        if solution is None or solution.empty:
            return solution

        neighbor = solution.copy()

        if len(neighbor) == 0:
            return neighbor

        # Выбор случайной операции мутации
        mutation_type = random.choice(['load', 'swap', 'type'])

        idx = random.randint(0, len(neighbor) - 1)

        try:
            if mutation_type == 'load' and 'teacher_load' in neighbor.columns:
                # Изменение нагрузки
                neighbor.loc[idx, 'teacher_load'] = neighbor.loc[idx, 'teacher_load'] * random.uniform(0.8, 1.2)

            elif mutation_type == 'swap' and len(neighbor) > 1:
                # Обмен двух записей
                idx2 = random.randint(0, len(neighbor) - 1)
                if idx != idx2:
                    # Создаем копии строк
                    row1 = neighbor.iloc[idx].copy()
                    row2 = neighbor.iloc[idx2].copy()
                    # Меняем местами
                    neighbor.iloc[idx] = row2
                    neighbor.iloc[idx2] = row1

            elif mutation_type == 'type' and 'lesson_type' in neighbor.columns:
                # Смена типа занятия
                types = ['Лекция', 'Семинар', 'Лабораторная']
                current_type = neighbor.loc[idx, 'lesson_type']
                other_types = [t for t in types if t != current_type]
                if other_types:
                    neighbor.loc[idx, 'lesson_type'] = random.choice(other_types)
        except Exception as e:
            # Если ошибка, возвращаем исходное решение
            pass

        return neighbor

    def calculate_fitness(self, solution, teachers_df, classrooms_df):
        """Расчет fitness для решения"""
        if solution is None or solution.empty:
            return 0

        result = self.fitness_calculator.calculate_fitness(
            solution, teachers_df, classrooms_df
        )
        return result['fitness']

    def acceptance_probability(self, delta_fitness, temperature):
        """Вероятность принятия худшего решения"""
        if delta_fitness >= 0:
            return 1.0
        if temperature <= 0:
            return 0
        try:
            return math.exp(delta_fitness / temperature)
        except:
            return 0

    def run(self, initial_solution, teachers_df, classrooms_df):
        """Запуск алгоритма имитации отжига"""
        print(f"🔥 Запуск алгоритма имитации отжига:")
        print(f"   Начальная температура: {self.initial_temperature}")
        print(f"   Коэффициент охлаждения: {self.cooling_rate}")

        if initial_solution is None or initial_solution.empty:
            print("   ⚠️ Нет данных для оптимизации")
            return initial_solution

        try:
            current_solution = initial_solution.copy()
            current_fitness = self.calculate_fitness(
                current_solution, teachers_df, classrooms_df
            )

            best_solution = current_solution.copy()
            best_fitness = current_fitness

            temperature = self.initial_temperature
            iteration = 0

            while temperature > self.min_temperature and iteration < self.max_iterations:
                self.temperature_history.append(temperature)
                self.fitness_history.append(best_fitness)

                # Генерация соседнего решения
                neighbor = self.generate_neighbor(
                    current_solution, teachers_df, classrooms_df
                )

                if neighbor is not None and not neighbor.empty:
                    neighbor_fitness = self.calculate_fitness(
                        neighbor, teachers_df, classrooms_df
                    )

                    # Расчет изменения
                    delta_fitness = neighbor_fitness - current_fitness

                    # Решение о принятии
                    if delta_fitness > 0:
                        current_solution = neighbor
                        current_fitness = neighbor_fitness

                        if current_fitness > best_fitness:
                            best_solution = current_solution.copy()
                            best_fitness = current_fitness
                    else:
                        prob = self.acceptance_probability(delta_fitness, temperature)
                        if random.random() < prob:
                            current_solution = neighbor
                            current_fitness = neighbor_fitness

                # Охлаждение
                temperature *= self.cooling_rate
                iteration += 1

                # Логирование
                if iteration % 200 == 0:
                    print(f"   Итерация {iteration}: "
                          f"T = {temperature:.2f}, "
                          f"Best Fitness = {best_fitness:.4f}")
        except Exception as e:
            print(f"   ⚠️ Ошибка в алгоритме: {e}")
            best_solution = initial_solution

        print(f"✅ Алгоритм имитации отжига завершен")
        print(f"   Лучший Fitness: {best_fitness:.4f}")
        print(f"   Итераций: {iteration}")

        return best_solution