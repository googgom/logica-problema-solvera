import os
import subprocess

def run_test(test_case, index):
    # Записываем тест в input.txt
    with open("input.txt", "w", encoding="utf-8") as f:
        f.write(test_case)

    # Запускаем main.py
    try:
        subprocess.run(["python3", "main.py"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Тест {index + 1} не выполнен: ошибка при запуске main.py")
        return False

    # Проверяем output.txt на наличие подстроки
    try:
        with open("output.txt", "r", encoding="utf-8") as f:
            content = f.read()
            if "мы доказали - True" in content:
                print(f"Тест {index + 1} выполнен успешно.")
                return True
            else:
                print(f"Тест {index + 1} не выполнен: в output.txt нет подстроки 'мы доказали - True'.")
                return False
    except FileNotFoundError:
        print(f"Тест {index + 1} не выполнен: файл output.txt не найден.")
        return False

def main():
    # Импортируем тесты из tests/problem.py
    from tests.problem import problem

    passed = 0
    for i, test in enumerate(problem):
        if run_test(test, i):
            passed += 1

    print(f"\nВыполнено {passed} из {len(problem)} тестов.")

if __name__ == "__main__":
    main()
