import itertools
import json
import re

class Term:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args if args is not None else []

    def __repr__(self):
        if not self.args:
            return str(self.name)
        return f"{self.name}({', '.join(map(str, self.args))})"

    def __eq__(self, other):
        return isinstance(other, Term) and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

    # Применение подстановки к терму
    def apply_substitution(self, substitution):
        if isinstance(self.name, str) and self.name in substitution:
            substituted = substitution[self.name]
            if isinstance(substituted, Term):
                return substituted.apply_substitution(substitution)
            return substituted
        new_args = [arg.apply_substitution(substitution) if isinstance(arg, Term) else substitution.get(arg, arg) for arg in self.args]
        return Term(self.name, new_args)

    # Проверка на наличие переменной в терме
    def occurs_check(self, var):
        if isinstance(self.name, str) and self.name == var:
            return True
        for arg in self.args:
            if isinstance(arg, Term) and arg.occurs_check(var):
                return True
            if arg == var:
                return True
        return False

class Literal:
    # Процедура создания литерала. negated - флаг отрицания
    def __init__(self, predicate, args, negated=False):
        self.predicate = predicate
        self.args = args
        self.negated = negated

    # Возврат строки в читаемом виде
    def __repr__(self):
        return ("¬" if self.negated else "") + f"{self.predicate}({', '.join(map(str, self.args))})"

    # Процедура сравнения
    def __eq__(self, other):
        return (self.predicate == other.predicate and
                self.args == other.args and
                self.negated == other.negated)

    # Хеш для встроенных структур данных
    def __hash__(self):
        return hash((self.predicate, tuple(self.args), self.negated))

    # Вернёт отрицание
    def negate(self):
        return Literal(self.predicate, self.args, not self.negated)

    # Встроенное сравнение "противоречия"
    def is_negation_of(self, other):
        return self.predicate == other.predicate and self.negated != other.negated

    # Применение подстановки к литералу
    def apply_substitution(self, substitution):
        new_args = []
        for arg in self.args:
            if isinstance(arg, Term):
                new_args.append(arg.apply_substitution(substitution))#Или применяем подстановку(если она есть)
            elif arg in substitution:
                new_args.append(substitution[arg])#Или добавляем подстановку(если она есть)
            else:
                new_args.append(arg)#Или оставляем аргумент в изначальном виде
        return Literal(self.predicate, new_args, self.negated)

    # Для JSON
    def to_dict(self):
        return {
            "predicate": self.predicate,
            "args": [arg.to_dict() if isinstance(arg, Term) else arg for arg in self.args],
            "negated": self.negated
        }

class Clause:
    def __init__(self, literals):
        self.literals = literals

    # Читаемый вид
    def __repr__(self):
        return " ∨ ".join(map(str, self.literals))

    # Сравнил быстро и мощно
    def __eq__(self, other):
        return set(self.literals) == set(other.literals)

    # Хеш для std
    def __hash__(self):
        return hash(frozenset(self.literals))

    # Для JSON
    def to_dict(self):
        return {
            "literals": [literal.to_dict() for literal in self.literals]
        }

# Унификация аргументов
def unify_args(a1, a2, substitution, step=1, log=None):
    if log is None:
        log = []

    if substitution is None:
        log.append(f"Шаг {step}: Унификация невозможна.")
        return None, log

    # Применяем текущую подстановку к аргументам
    if isinstance(a1, str) and a1 in substitution:
        a1 = substitution[a1]
    if isinstance(a2, str) and a2 in substitution:
        a2 = substitution[a2]

    if a1 == a2:
        log.append(f"Шаг {step}: {a1} и {a2} уже унифицированы.")
        return substitution, log

    if isinstance(a1, str) and a1.islower():
        if isinstance(a2, Term) and a2.occurs_check(a1):
            log.append(f"Шаг {step}: Циклическая подстановка: переменная {a1} входит в терм {a2}.")
            return None, log
        log.append(f"Шаг {step}: Переменная {a1} связана с {a2}.")
        return {**substitution, a1: a2}, log

    if isinstance(a2, str) and a2.islower():
        if isinstance(a1, Term) and a1.occurs_check(a2):
            log.append(f"Шаг {step}: Циклическая подстановка: переменная {a2} входит в терм {a1}.")
            return None, log
        log.append(f"Шаг {step}: Переменная {a2} связана с {a1}.")
        return {**substitution, a2: a1}, log

    if isinstance(a1, Term) and isinstance(a2, Term):
        if a1.name != a2.name or len(a1.args) != len(a2.args):
            log.append(f"Шаг {step}: Унификация {a1} и {a2} невозможна: разные имена или количество аргументов.")
            return None, log

        log.append(f"Шаг {step}: Унификация термов {a1} и {a2}.")
        for i, (arg1, arg2) in enumerate(zip(a1.args, a2.args)):
            substitution, log = unify_args(arg1, arg2, substitution, step + i + 1, log)
            if substitution is None:
                return None, log
        return substitution, log

    log.append(f"Шаг {step}: Унификация {a1} и {a2} невозможна: несовместимые типы.")
    return None, log

# Унификация литералов
def unify(l1, l2, substitution):
    # Проверка по умолчанию - смысла в ней вероятно уже нет, но и вреда тоже
    if substitution is None:
        return None

    # Предикаты должны совпадать, а знаки отличаться
    if l1.predicate != l2.predicate or l1.negated == l2.negated:
        return None

    # Аргументов должно быть поровну
    if len(l1.args) != len(l2.args):
        return None

    # Если хотя бы одна пара аргументов не может быть унифицирована, то и вся унификация литералов невозможна
    for a1, a2 in zip(l1.args, l2.args):
        substitution, _ = unify_args(a1, a2, substitution)
        if substitution is None:
            return None
    return substitution

# Применение подстановки к литералу
def apply_substitution(literal, substitution):
    return literal.apply_substitution(substitution)

# Резолюция двух клауз
def resolve(c1, c2):
    # Создаёт все пары из литералов
    for l1, l2 in itertools.product(c1.literals, c2.literals):
        if l1.is_negation_of(l2):# Условие резолюции - противоположные знаки
            substitution = unify(l1, l2, {})
            if substitution is not None:# Ищем подстановку, что бы резольвировать
                new_literals = []
                for lit in c1.literals + c2.literals:# Собираем не выбранные литералы для применения к ним подстановки
                    if lit != l1 and lit != l2:
                        new_literals.append(apply_substitution(lit, substitution))
                return Clause(new_literals), substitution# Новая клауза - результат резолюции и подстановка для лога
    return None, None

# Алгоритм резолюции
def resolution(clauses, max_steps=50):
    log = []
    step = 1
    clauses = list(set(clauses)) # Убираем дубликаты клауз!
    for _ in range(max_steps):
        new_clauses = []
        for c1, c2 in itertools.combinations(clauses, 2):
            new_clause, substitution = resolve(c1, c2)
            if new_clause is not None:
                if not new_clause.literals:
                    log.append(f"Шаг {step}: Резолюция {c1} и {c2} -> Противоречие.")
                    return True, log
                if new_clause not in clauses and new_clause not in new_clauses:
                    log.append(f"Шаг {step}: Унификация {substitution} в {c1} и {c2}. Резолюция -> {new_clause}.")
                    step += 1
                    new_clauses.append(new_clause)
        if not new_clauses:# Если нет прогресса в итерации, то уже и не будет
            return False, log
        clauses += new_clauses
    # Для возможных случаев, когда новые уникальные клаузы создаются, но решение не приближают
    print("ВНИМАНИЕ: Превышено ограничение на количество итераций резолюции.")
    print("Вероятно ответа не существует или время его нахождения слишком большое.")
    print(f"На данный момент хранится {len(clauses)} клауз.")
    print("Если хотите продолжить поиск противоречия, введите 'continue'")
    temp = input()
    if temp == 'continue':# Если пользователь решит продолжить поиск
        proof2, log2 = resolution(clauses)
        log2 += log
        return proof2, log2
    return False, log

# Чтение клауз из JSON
def read_clauses(filename):
    with open(filename, "r", encoding="utf-8") as f:
        loaded_clauses_dict = json.load(f)
    def dict_to_term(d):
        if isinstance(d, dict):
            return Term(d["name"], [dict_to_term(arg) for arg in d["args"]])
        return d
    def dict_to_literal(d):
        args = [dict_to_term(arg) if isinstance(arg, dict) else arg for arg in d["args"]]
        return Literal(d["predicate"], args, d["negated"])
    def dict_to_clause(d):
        return Clause([dict_to_literal(literal) for literal in d["literals"]])
    loaded_clauses = [dict_to_clause(clause) for clause in loaded_clauses_dict]
    return loaded_clauses

# Запись лога в файл
def write_log(log, proof, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Лог шагов:\n")
        for entry in log:
            f.write(f"{entry}\n")
        f.write(f"Противоречие найдено: {proof}\n")

# Разбор терма из строки
def parse_term(term_str):
    term_str = term_str.strip()
    if not term_str:
        return None
    # Проверка на переменную или константу
    if '(' not in term_str:
        return term_str
    # Разбор вложенного терма
    name_end = term_str.find('(')
    name = term_str[:name_end]
    args_str = term_str[name_end+1:-1]
    args = []
    bracket_level = 0
    current_arg = []
    for char in args_str:
        if char == '(':
            bracket_level += 1
            current_arg.append(char)
        elif char == ')':
            bracket_level -= 1
            current_arg.append(char)
        elif char == ',' and bracket_level == 0:
            args.append(parse_term(''.join(current_arg).strip()))
            current_arg = []
        else:
            current_arg.append(char)
    if current_arg:
        args.append(parse_term(''.join(current_arg).strip()))
    return Term(name, args)

# Разбор литерала из строки
def parse_literal(literal_str):
    literal_str = literal_str.strip()
    if literal_str.startswith('¬'):
        negated = True
        literal_str = literal_str[1:].strip()
    else:
        negated = False
    predicate_end = literal_str.find('(')
    if predicate_end == -1:
        predicate = literal_str
        args = []
    else:
        predicate = literal_str[:predicate_end]
        args_str = literal_str[predicate_end+1:-1]
        args = []
        bracket_level = 1 if args_str else 0
        current_arg = []
        for char in args_str:
            if char == '(':
                bracket_level += 1
                current_arg.append(char)
            elif char == ')':
                bracket_level -= 1
                current_arg.append(char)
            elif char == ',' and bracket_level == 1:
                args.append(parse_term(''.join(current_arg).strip()))
                current_arg = []
            else:
                current_arg.append(char)
        if current_arg:
            args.append(parse_term(''.join(current_arg).strip()))
    return Literal(predicate, args, negated)

# Чтение двух формул из консоли
def read_formulas():
    print("Введите первую формулу:")
    formula1 = input().strip()
    print("Введите вторую формулу:")
    formula2 = input().strip()
    literal1 = parse_literal(formula1)
    literal2 = parse_literal(formula2)
    return [literal1, literal2]

# Унификация двух формул с выводом шагов и применением подстановки
def unify_formulas(formulas):
    l1, l2 = formulas
    if l1.predicate != l2.predicate:
        print(f"Унификация невозможна: предикаты {l1.predicate} и {l2.predicate} не совпадают.")
        return
    if len(l1.args) != len(l2.args):
        print(f"Унификация невозможна: количество аргументов не совпадает.")
        return

    substitution = {}
    log = []
    log.append(f"Начало унификации формул: {l1} и {l2}.")

    for i, (a1, a2) in enumerate(zip(l1.args, l2.args)):
        substitution, log = unify_args(a1, a2, substitution, i + 1, log)
        if substitution is None:
            print("Унификация невозможна.")
            for entry in log:
                print(entry)
            return

    # Проверяем, что подстановка не содержит циклических зависимостей
    for var, term in substitution.items():
        if isinstance(term, Term) and term.occurs_check(var):
            print("Унификация невозможна: циклическая подстановка.")
            for entry in log:
                print(entry)
            return

    print(f"Унификация успешна. Подстановка: {substitution}")
    for entry in log:
        print(entry)

    # Применение подстановки к исходным формулам
    # Применяем подстановку последовательно, чтобы корректно заменить все переменные
    full_substitution = substitution.copy()
    changed = True
    while changed:
        changed = False
        for var, term in list(full_substitution.items()):
            if isinstance(term, str) and term in full_substitution:
                full_substitution[var] = full_substitution[term]
                changed = True
            elif isinstance(term, Term):
                new_term = term.apply_substitution(full_substitution)
                if new_term != term:
                    full_substitution[var] = new_term
                    changed = True

    print(f"Полная подстановка: {full_substitution}")

    l1_substituted = l1.apply_substitution(full_substitution)
    l2_substituted = l2.apply_substitution(full_substitution)
    print(f"Первая формула после подстановки: {l1_substituted}")
    print(f"Вторая формула после подстановки: {l2_substituted}")

    # Проверка на совпадение формул после подстановки
    if l1_substituted == l2_substituted:
        print("Формулы после подстановки совпадают.")
    else:
        print("Формулы после подстановки не совпадают.")

if __name__ == "__main__":
    # Пример использования функции read_formulas
    print("Пример унификации двух формул:")
    #formula1 = "P(f(g(f(a))), p(a, x), f(f(h(a, a, z))), g(x), f(p(ψ(c), r(x))))"
    #formula2 = "P(f(g(f(a))), p(t, q(b)), f(f(h(a, a, s(t)))), g(q(b)), f(p(y, u)))"
    #formula1 = "P(f(x), y)"
    #formula2 = "P(x, z)"
    #formula1 = "P(x, y)"
    #formula2 = "P(f(y), x)"
    #formula1 = "P(f(a,x))"
    #formula2 = "P(g(b,y))"
    formula1 = "P(f(x), x)"
    formula2 = "P(f(g(z)), g(y))"
    literal1 = parse_literal(formula1)
    literal2 = parse_literal(formula2)
    print(f"Первая формула: {literal1}")
    print(f"Вторая формула: {literal2}")
    unify_formulas([literal1, literal2])

    # Основной режим работы
    clauses = read_clauses("input.txt")
    proof, log = resolution(clauses)
    write_log(log, proof, "output.txt")
    print("Модуль II:")
    print("Лог шагов:")
    for entry in log:
        print(entry)
    print("Противоречие найдено:", proof)