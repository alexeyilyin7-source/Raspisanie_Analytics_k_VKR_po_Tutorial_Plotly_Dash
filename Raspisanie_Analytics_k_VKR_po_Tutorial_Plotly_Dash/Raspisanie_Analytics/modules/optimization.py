# modules/optimization.py
from modules.genetic_algorithm import GeneticAlgorithm
from modules.simulated_annealing import SimulatedAnnealing  # Правильный относительный импорт с точкой
from modules.greedy_algorithm import GreedyAlgorithm
from modules.fitness_calculator import FitnessCalculator
from modules.schedule_validator import ScheduleValidator
import pandas as pd


class OptimizationEngine:
    """Основной движок оптимизации, объединяющий все алгоритмы"""

    def __init__(self):
        self.ga = GeneticAlgorithm(
            population_size=30,
            generations=50,
            mutation_rate=0.1,
            crossover_rate=0.8
        )
        self.sa = SimulatedAnnealing(
            initial_temperature=100.0,
            cooling_rate=0.95,
            min_temperature=0.1,
            max_iterations=500
        )
        self.greedy = GreedyAlgorithm()
        self.fitness_calculator = FitnessCalculator()
        self.validator = ScheduleValidator()

    def optimize(self, base_data, teachers_df, groups_df, classrooms_df,
                 algorithm='auto', validate=True):
        """
        Запуск оптимизации выбранным алгоритмом

        algorithm: 'ga' - генетический
                  'sa' - имитация отжига
                  'greedy' - жадный
                  'auto' - комбинированный (по умолчанию)
        """
        print("=" * 60)
        print("🧠 ЗАПУСК ОПТИМИЗАЦИИ РАСПИСАНИЯ")
        print("=" * 60)

        result = None
        algorithm_used = algorithm

        if base_data.empty:
            print("⚠️ Нет данных для оптимизации")
            return {
                'schedule': base_data,
                'algorithm': algorithm_used,
                'fitness': None,
                'validation': None
            }

        try:
            if algorithm == 'greedy':
                # Только жадный алгоритм
                result = self.greedy.run(base_data, teachers_df, classrooms_df)

            elif algorithm == 'ga':
                # Только генетический
                result = self.ga.run(base_data, teachers_df, classrooms_df)

            elif algorithm == 'sa':
                # Только имитация отжига
                result = self.sa.run(base_data, teachers_df, classrooms_df)

            else:  # 'auto' - комбинированный подход
                print("\n📊 Этап 1: Быстрое построение (жадный алгоритм)")
                greedy_result = self.greedy.run(base_data, teachers_df, classrooms_df)

                print("\n🧬 Этап 2: Глобальная оптимизация (генетический алгоритм)")
                ga_result = self.ga.run(greedy_result, teachers_df, classrooms_df)

                print("\n🔥 Этап 3: Локальное улучшение (имитация отжига)")
                result = self.sa.run(ga_result, teachers_df, classrooms_df)

                algorithm_used = 'combined (greedy + ga + sa)'

            # Валидация результата
            if validate and result is not None and not result.empty:
                print("\n🔍 Этап 4: Валидация результата")
                is_valid, hard_violations = self.validator.check_hard_constraints(
                    result, teachers_df, groups_df, classrooms_df
                )
                soft_violations = self.validator.check_soft_constraints(
                    result, teachers_df
                )

                if is_valid:
                    print("   ✅ Все жесткие ограничения соблюдены")
                else:
                    print(f"   ⚠️ Нарушений жестких ограничений: {len(hard_violations)}")

                print(f"   ⚠️ Нарушений мягких ограничений: {len(soft_violations)}")

                # Итоговый fitness
                fitness_result = self.fitness_calculator.calculate_fitness(
                    result, teachers_df, classrooms_df
                )
                print(f"\n📈 Итоговая fitness: {fitness_result['fitness']:.4f}")
                print(f"   Общий штраф: {fitness_result['total_penalty']:.2f}")
                print("   Компоненты штрафа:")
                for comp, value in fitness_result['components'].items():
                    print(f"      - {comp}: {value:.2f}")
            else:
                fitness_result = None
        except Exception as e:
            print(f"❌ Ошибка при оптимизации: {e}")
            import traceback
            traceback.print_exc()
            result = base_data
            fitness_result = None

        print("=" * 60)
        print("✅ ОПТИМИЗАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)

        return {
            'schedule': result,
            'algorithm': algorithm_used,
            'fitness': fitness_result,
            'validation': self.validator.get_validation_report() if validate and hasattr(self, 'validator') else None
        }


# Глобальный экземпляр
optimization_engine = OptimizationEngine()