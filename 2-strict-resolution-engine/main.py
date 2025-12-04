import itertools
import json

class Term:
    def __init__(self, name, args=None):
        self.name = name
        self.args = args if args is not None else []

    def __repr__(self):
        if not self.args:
            return self.name
        return f"{self.name}({', '.join(map(str, self.args))})"

    def __eq__(self, other):
        return isinstance(other, Term) and self.name == other.name and self.args == other.args

    def __hash__(self):
        return hash((self.name, tuple(self.args)))

    def apply_substitution(self, substitution):
        if not self.args:
            if isinstance(self.name, str) and self.name in substitution:
                return substitution[self.name]
            return self
        new_args = [arg.apply_substitution(substitution) if isinstance(arg, Term) else substitution.get(arg, arg) for arg in self.args]
        return Term(self.name, new_args)

class Literal:
    #Процедура создания литерала. negated - флаг отрицания
    def __init__(self, predicate, args, negated=False):
        self.predicate = predicate
        self.args = args
        self.negated = negated

    #Возврат строки в читаемом виде
    def __repr__(self):
        return ("¬" if self.negated else "") + f"{self.predicate}({', '.join(map(str, self.args))})"

    #Процедура сравнения
    def __eq__(self, other):
        return (self.predicate == other.predicate and
                self.args == other.args and
                self.negated == other.negated)

    #Хеш для встроенных структур данных
    def __hash__(self):
        return hash((self.predicate, tuple(self.args), self.negated))

    #Вернёт отрицание
    def negate(self):
        return Literal(self.predicate, self.args, not self.negated)

    #Встроенное сравнение "противоречия"
    def is_negation_of(self, other):
        return self.predicate == other.predicate and self.negated != other.negated

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

    #Для JSON
    def to_dict(self):
        return {
            "predicate": self.predicate,
            "args": [arg.to_dict() if isinstance(arg, Term) else arg for arg in self.args],
            "negated": self.negated
        }


class Clause:
    def __init__(self, literals):
        self.literals = literals

    #Читаемый вид
    def __repr__(self):
        return " ∨ ".join(map(str, self.literals))

    #Сравнил быстро и мощно
    def __eq__(self, other):
        return set(self.literals) == set(other.literals)

    #Хеш для std
    def __hash__(self):
        return hash(frozenset(self.literals))

    #Для JSON
    def to_dict(self):
        return {
            "literals": [literal.to_dict() for literal in self.literals]
        }

def unify_args(a1, a2, substitution):
    #Проверка по умолчанию - смысла в ней вероятно уже нет, но и вреда тоже
    if substitution is None:
        return None
    #Одинаковые аргументы - нечего подставлять - всё и так нормально
    if a1 == a2:
        return substitution
    #Определяет переменную и подставляет значение(или другую переменную), затем добавляет её в список подстановок
    if isinstance(a1, str) and a1.islower():
        return {**substitution, a1: a2}
    if isinstance(a2, str) and a2.islower():
        return {**substitution, a2: a1}
    if isinstance(a1, Term) and isinstance(a2, Term):
        if a1.name != a2.name or len(a1.args) != len(a2.args):
            return None
        for arg1, arg2 in zip(a1.args, a2.args):
            substitution = unify_args(arg1, arg2, substitution)
            if substitution is None:
                return None
        return substitution
    return None


def unify(l1, l2, substitution):
    #Проверка по умолчанию - смысла в ней вероятно уже нет, но и вреда тоже
    if substitution is None:
        return None
    #Предикаты должны совпадать, а знаки отличаться
    if l1.predicate != l2.predicate or l1.negated == l2.negated:
        return None
    #Аргументов должно быть поровну
    if len(l1.args) != len(l2.args):
        return None

    #Если хотя бы одна пара аргументов не может быть унифицирована, то и вся унификация литералов невозможна
    for a1, a2 in zip(l1.args, l2.args):
        substitution = unify_args(a1, a2, substitution)
        if substitution is None:
            return None
    return substitution

def apply_substitution(literal, substitution):
    return literal.apply_substitution(substitution)

def resolve(c1, c2):
    #Создаёт все пары из литералов
    for l1, l2 in itertools.product(c1.literals, c2.literals):
        if l1.is_negation_of(l2):#Условие резолюции - противоположные знаки
            substitution = unify(l1, l2, {})
            if substitution is not None:#Ищем подстановку, что бы резольвировать
                new_literals = []
                for lit in c1.literals + c2.literals:#Собираем не выбранные литералы для применения к ним подстановки
                    if lit != l1 and lit != l2:
                        new_literals.append(apply_substitution(lit, substitution))
                return Clause(new_literals), substitution#Новая клауза - результат резолюции и подстановка для лога
    return None, None

def resolution(clauses, max_steps=50):
    log = []
    step = 1
    clauses = list(set(clauses)) #Убираем дубликаты клауз!
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
        if not new_clauses:#Если нет прогресса в итерации, то уже и не будет
            return False, log
        clauses += new_clauses
    #Для возможных случаев, когда новые уникальные клаузы создаются, но решение не приближают
    print("ВНИМАНИЕ: Превышено ограничение на количество итераций резолюции.")
    print("Вероятно ответа не существует или время его нахождения слишком большое.")
    print(f"На данный момент храниться {len(clauses)} клауз.")
    print("Если хотите продолжить поиск противоречия введите 'continue'")
    temp = input()
    if temp == 'continue':#Если пользователь решит продолжить поиск
        proof2, log2 = resolution(clauses)
        log2 += log
        return proof2, log2
    return False, log

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


def write_log(log, proof, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Лог шагов:\n")
        for entry in log:
            f.write(f"{entry}\n")
        f.write(f"Противоречие найдено: {proof}\n")



if __name__ == "__main__":
    #Основной режим работы
    clauses = read_clauses("input.txt")

    proof, log = resolution(clauses)
    write_log(log, proof, "output.txt")
    print("Модуль II:")
    print("Лог шагов:")
    for entry in log:
        print(entry)
    print("Противоречие найдено:", proof)

