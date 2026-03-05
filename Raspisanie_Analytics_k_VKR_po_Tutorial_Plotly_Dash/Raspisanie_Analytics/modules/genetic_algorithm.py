# modules/genetic_algorithm.py
import numpy as np
import pandas as pd
import random
from modules.fitness_calculator import FitnessCalculator


class GeneticAlgorithm:
    """Реализация генетического алгоритма для оптимизации расписания"""

    def __init__(self, population_size=50, generations=100,
                 mutation_rate=0.1, crossover_rate=0.8):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.fitness_calculator = FitnessCalculator()
        self.best_fitness_history = []
        self.avg_fitness_history = []

    def initialize_population(self, base_data, teachers_df, classrooms_df):
        """Создание начальной популяции"""
        population = []

        for _ in range(self.population_size):
            # Создание случайного расписания на основе базовых данных
            individual = base_data.copy()

            # Случайные мутации для разнообразия
            if len(individual) > 0:
                # Случайное изменение нагрузки для некоторых записей
                n_mutations = min(5, len(individual))
                indices = random.sample(range(len(individual)), n_mutations) if len(individual) > n_mutations else list(
                    range(len(individual)))
                for idx in indices:
                    if 'teacher_load' in individual.columns:
                        individual.loc[idx, 'teacher_load'] *= random.uniform(0.8, 1.2)

            population.append(individual)

        return population

    def calculate_individual_fitness(self, individual, teachers_df, classrooms_df):
        """Расчет fitness для одной особи"""
        result = self.fitness_calculator.calculate_fitness(
            individual, teachers_df, classrooms_df
        )
        return result['fitness']

    def selection(self, population, fitness_scores):
        """Селекция особей (турнирный отбор)"""
        selected = []
        pop_size = len(population)
        for _ in range(self.population_size):
            # Турнир из 3 случайных особей
            tournament_size = min(3, pop_size)
            tournament_indices = random.sample(range(pop_size), tournament_size)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            winner_idx = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(population[winner_idx].copy())
        return selected

    def crossover(self, parent1, parent2):
        """Скрещивание (кроссинговер) двух родителей"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()

        child1 = parent1.copy()
        child2 = parent2.copy()

        # Одноточечный кроссинговер
        if len(parent1) > 1 and len(parent2) > 1:
            point = random.randint(1, min(len(parent1), len(parent2)) - 1)

            # Обмен частями расписаний
            temp1 = child1.iloc[point:].copy()
            temp2 = child2.iloc[point:].copy()

            for i in range(point, len(child1)):
                if i < len(child2):
                    child1.iloc[i] = parent2.iloc[i]
            for i in range(point, len(child2)):
                if i < len(parent1):
                    child2.iloc[i] = parent1.iloc[i]

        return child1, child2

    def mutation(self, individual):
        """Мутация особи"""
        if random.random() > self.mutation_rate:
            return individual

        mutated = individual.copy()

        if len(mutated) > 0:
            # Случайное изменение одной записи
            idx = random.randint(0, len(mutated) - 1)

            # Мутация нагрузки
            if 'teacher_load' in mutated.columns:
                mutated.loc[idx, 'teacher_load'] *= random.uniform(0.7, 1.3)

            # Мутация типа занятия (если есть)
            if 'lesson_type' in mutated.columns:
                types = ['Лекция', 'Семинар', 'Лабораторная']
                current_type = mutated.loc[idx, 'lesson_type']
                other_types = [t for t in types if t != current_type]
                if other_types:
                    mutated.loc[idx, 'lesson_type'] = random.choice(other_types)

        return mutated

    def run(self, base_data, teachers_df, classrooms_df):
        """Запуск генетического алгоритма"""
        print(f"🚀 Запуск генетического алгоритма:")
        print(f"   Популяция: {self.population_size}")
        print(f"   Поколений: {self.generations}")
        print(f"   Мутация: {self.mutation_rate}")

        if base_data.empty:
            print("   Нет данных для оптимизации")
            return base_data

        # Инициализация
        population = self.initialize_population(base_data, teachers_df, classrooms_df)

        for generation in range(self.generations):
            # Расчет fitness
            fitness_scores = [
                self.calculate_individual_fitness(ind, teachers_df, classrooms_df)
                for ind in population
            ]

            # Сохранение статистики
            self.best_fitness_history.append(max(fitness_scores))
            self.avg_fitness_history.append(np.mean(fitness_scores))

            # Селекция
            selected = self.selection(population, fitness_scores)

            # Скрещивание и мутация
            next_population = []
            for i in range(0, self.population_size, 2):
                if i + 1 < len(selected):
                    child1, child2 = self.crossover(selected[i], selected[i + 1])
                    child1 = self.mutation(child1)
                    child2 = self.mutation(child2)
                    next_population.extend([child1, child2])
                else:
                    next_population.append(selected[i].copy())

            population = next_population[:self.population_size]

            # Логирование
            if generation % 20 == 0:
                print(f"   Поколение {generation}: "
                      f"Best Fitness = {self.best_fitness_history[-1]:.4f}, "
                      f"Avg Fitness = {self.avg_fitness_history[-1]:.4f}")

        # Возврат лучшего решения
        final_fitness = [
            self.calculate_individual_fitness(ind, teachers_df, classrooms_df)
            for ind in population
        ]
        best_idx = np.argmax(final_fitness)

        print(f"✅ Генетический алгоритм завершен")
        print(f"   Лучший Fitness: {final_fitness[best_idx]:.4f}")

        return population[best_idx]