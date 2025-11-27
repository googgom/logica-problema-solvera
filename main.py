import os
import shutil
import subprocess
import requests
from numpy.random import random_integers
from tests.problem import *
import random


def launch():
    if not os.path.exists("input.txt") or os.path.getsize("input.txt") == 0:
        com = int(input("Выберите сложность(1-3):")) - 1
        index = random.randint(1, 3)
        index = index + com * 3 - 1
        with open("input.txt", "w", encoding='utf-8') as f:
            f.write(problem[index])
        return index
    else:
        with open("input.txt", "r", encoding='utf-8') as f:
            return f.read()


def main():
    # Путь к текущему каталогу
    base_dir = os.path.dirname(os.path.abspath(__file__))

    launch()

    with open("input.txt", 'r', encoding='utf-8') as f:
        print(f.read())

    # Шаг 1: Копируем input.txt в 1-rus-to-log/input.txt
    input_path = os.path.join(base_dir, "input.txt")
    module1_input_path = os.path.join(base_dir, "1-rus-to-log", "input.txt")

    if os.path.exists(input_path):
        shutil.copy(input_path, module1_input_path)
        print(f"Скопирован {input_path} в {module1_input_path}")
    else:
        print(f"Ошибка: файл {input_path} не найден.")
        return


    # Шаг 2: Запускаем main.py в каталоге 1-rus-to-log
    module1_main_path = os.path.join(base_dir, "1-rus-to-log", "main.py")
    if os.path.exists(module1_main_path):
        subprocess.run(["python", module1_main_path], cwd=os.path.join(base_dir, "1-rus-to-log"))
        print(f"Запущен {module1_main_path}")
    else:
        print(f"Ошибка: файл {module1_main_path} не найден.")
        return

    # Шаг 3: Копируем output.txt из 1-rus-to-log в input.txt для 2-strict-resolution-engine
    module1_output_path = os.path.join(base_dir, "1-rus-to-log", "output.txt")
    module2_input_path = os.path.join(base_dir, "2-strict-resolution-engine", "input.txt")

    if os.path.exists(module1_output_path):
        shutil.copy(module1_output_path, module2_input_path)
        print(f"Скопирован {module1_output_path} в {module2_input_path}")
    else:
        print(f"Ошибка: файл {module1_output_path} не найден.")
        return

    # Шаг 4: Запускаем main.py в каталоге 2-strict-resolution-engine
    module2_main_path = os.path.join(base_dir, "2-strict-resolution-engine", "main.py")
    if os.path.exists(module2_main_path):
        subprocess.run(["python", module2_main_path], cwd=os.path.join(base_dir, "2-strict-resolution-engine"))
        print(f"Запущен {module2_main_path}")
    else:
        print(f"Ошибка: файл {module2_main_path} не найден.")
        return

    # Шаг 5: Копируем output.txt из 2-strict-resolution-engine в input.txt для 3-log-to-rus
    module2_output_path = os.path.join(base_dir, "2-strict-resolution-engine", "output.txt")
    module3_input_path = os.path.join(base_dir, "3-log-to-rus", "input.txt")

    if os.path.exists(module2_output_path):
        shutil.copy(module2_output_path, module3_input_path)
        print(f"Скопирован {module2_output_path} в {module3_input_path}")
    else:
        print(f"Ошибка: файл {module2_output_path} не найден.")
        return

    # Шаг 6: Запускаем main.py в каталоге 3-log-to-rus
    module3_main_path = os.path.join(base_dir, "3-log-to-rus", "main.py")
    if os.path.exists(module3_main_path):
        subprocess.run(["python", module3_main_path], cwd=os.path.join(base_dir, "3-log-to-rus"))
        print(f"Запущен {module3_main_path}")
    else:
        print(f"Ошибка: файл {module3_main_path} не найден.")
        return

    # Шаг 7: Копируем output.txt из 3-log-to-rus в output.txt текущего каталога
    module3_output_path = os.path.join(base_dir, "3-log-to-rus", "output.txt")
    final_output_path = os.path.join(base_dir, "output.txt")

    if os.path.exists(module3_output_path):
        shutil.copy(module3_output_path, final_output_path)
        print(f"Скопирован {module3_output_path} в {final_output_path}")
    else:
        print(f"Ошибка: файл {module3_output_path} не найден.")
        return

    # Шаг 8: Выводим содержимое output.txt в терминал
    if os.path.exists(final_output_path):
        with open(final_output_path, "r", encoding="utf-8") as file:
            print("\nСодержимое output.txt:")
            print(file.read())
    else:
        print(f"Ошибка: файл {final_output_path} не найден.")

if __name__ == "__main__":
    main()
