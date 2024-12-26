import numpy as np
import pandas as pd


class AdaptiveIntervalTracker:
    def __init__(self, granularity, tolerance=0.05, lock_threshold=8, max_buffer=20, p=0.2):
        """
        :param granularity: Кратность интервала (например, 0.05).
        :param tolerance: Допустимый размер интервала в процентах от текущего значения.
        :param lock_threshold: Число значений, на которое фиксируется интервал.
        :param max_buffer: Максимальное количество значений в буфере для анализа трендов.
        :param p: значимость нового интервала (определяет, нужно ли изменять интервал или нет)
        """
        self.granularity = granularity
        self.p = p
        self.tolerance = tolerance
        self.lock_threshold = lock_threshold
        self.max_buffer = max_buffer
        self.current_interval = None
        self.lock_count = 0  # Счётчик фиксации интервала
        self.buffer = []  # Список последних значений для анализа тренда

    def _round_to_granularity(self, value):
        """Округление значения до заданной кратности."""
        return round(value / self.granularity) * self.granularity

    def _calculate_interval(self, values):
        """Рассчитывает оптимальный интервал для заданных значений."""
        min_value = min(values)
        max_value = max(values)
        center = self._round_to_granularity((min_value + max_value) / 2)
        interval_size = max(self.granularity, self.tolerance * abs(center))
        lower_bound = self._round_to_granularity(center - interval_size / 2)
        upper_bound = self._round_to_granularity(center + interval_size / 2)
        return lower_bound, upper_bound

    def update_interval(self, value):
        """
        Обновляет интервал на основе нового значения.
        :param value: Новое значение.
        :return: Текущий интервал.
        """
        # Добавляем значение в буфер
        self.buffer.append(value)
        if len(self.buffer) > self.max_buffer:
            self.buffer.pop(0)

        if self.current_interval is None:
            # Если интервал ещё не установлен, инициализируем его
            self.current_interval = self._calculate_interval([value])
            self.lock_count = self.lock_threshold
            return self.current_interval

        if self.lock_count > 0:
            # Если интервал зафиксирован, проверяем, входит ли значение в текущий интервал
            if not (self.current_interval[0] <= value <= self.current_interval[1]):
                # Если значение выходит за пределы интервала, проверяем тренд
                trend_values = self.buffer[-self.max_buffer:]
                new_interval = self._calculate_interval(trend_values)
                if self._is_significant_change(new_interval):
                    # Если тренд существенно отличается, обновляем интервал
                    self.current_interval = new_interval
                    self.lock_count = self.lock_threshold
            self.lock_count -= 1
        else:
            # Если блокировка завершилась, пересчитываем интервал
            trend_values = self.buffer[-self.max_buffer:]
            new_interval = self._calculate_interval(trend_values)
            if new_interval != self.current_interval:
                self.current_interval = new_interval
                self.lock_count = self.lock_threshold

        return self.current_interval

    def _is_significant_change(self, new_interval):
        """
        Проверяет, является ли изменение интервала значительным.
        :param new_interval: Новый интервал.
        :return: True, если изменение значительное, иначе False.
        """
        if self.current_interval is None:
            return True
        # Сравниваем разницу текущего и нового интервалов
        current_range = self.current_interval[1] - self.current_interval[0]
        new_range = new_interval[1] - new_interval[0]
        # 50% изменения
        return abs(new_range - current_range) > self.p * current_range


# df = pd.read_csv('df_hack_fineal_fillna.csv')
# df_test = pd.read_csv('test.csv')
# feat_test = df_test['MEAS_DT']
# feat = df['Ni_1.1C']

# Пример использования

# tracker = AdaptiveIntervalTracker(
#     granularity=0.1, tolerance=0.2, lock_threshold=8, max_buffer=3, p=0.2)

# # Поток данных
# data_stream = feat
# current_interval_min = []
# current_interval_max = []
# for value in data_stream:
#     current_interval = tracker.update_interval(value)
#     current_interval_min.append(current_interval[0])
#     current_interval_max.append(current_interval[1])

# Проверка точности и оптимизации модели
# Q = 0
# Mean = []
# for j in range(0, len(df)):
#     if feat[j] < current_interval_min[j] or feat[j] > current_interval_max[j]:
#         Q += 1
#     Mean.append(current_interval_max[j] - current_interval_min[j])
# #print(f'{i} {round(current_interval_min[i],2)} {feat[i]} {round(current_interval_max[i],2)}')
# print('Вероятность ошибки: ', Q/len(df))
# print('Среднее расстояние между концами интервалов: ', np.mean(Mean))
