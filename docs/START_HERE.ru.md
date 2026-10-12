# Как пользоваться LeetCode Lab

Локальная папка: `D:\Study\leetcode`.
Публичный репозиторий: [dormyyy/leetcode-lab](https://github.com/dormyyy/leetcode-lab).

## 1. Создай папку задачи

Открой терминал в корне репозитория:

```powershell
cd D:\Study\leetcode
python tools/leetcode.py new 1 two-sum --title "Two Sum" --difficulty Easy --topics array hash-table
```

`1` — номер задачи, `two-sum` — часть её адреса на LeetCode. Сложность: `Easy`, `Medium` или `Hard`. Темы необязательны. Если Python вызывается через `py`, замени `python` на `py` во всех командах.

Появится `problems/0001-two-sum/`. В другой задаче будет другой номер и название. Команда не перезаписывает существующие задачи.

## 2. Решай на C++

- В `solution.cpp` вставь сигнатуру метода из LeetCode и напиши решение.
- В `main.cpp` добавь вызовы и проверки. Для связных списков или деревьев объяви `ListNode` / `TreeNode` **до** `#include "solution.cpp"`.
- В README задачи опиши идею, почему она работает, сложность и свои выводы. Можно писать на русском или английском.

В CLion открой корень `D:\Study\leetcode`, выбери свой C++ toolchain, перезагрузи CMake и запускай цель `problem_0001-two-sum`. Все задачи собираются независимо, поэтому их классы `Solution` не конфликтуют.

Первоначальный `main.cpp` сообщает, что проверок ещё нет. Добавь реальные случаи, прежде чем считать решение проверенным. На LeetCode отправляй содержимое `solution.cpp`.

Можно сохранять несколько подходов рядом: например, `solution.cpp` и `solution_bruteforce.cpp`. Для локального запуска включай нужный файл в `main.cpp`.

## 3. Отметь Accepted

После успешной отправки на LeetCode:

```powershell
python tools/leetcode.py done 1
```

Это отметит задачу как `solved`, запишет дату и обновит таблицу в корневом README. Если повторно запустить команду, первоначальная дата сохранится.

Статусы в `problem.json`:

| Статус | Значение |
| --- | --- |
| `planned` | Планирую решить |
| `in-progress` | Работаю над решением |
| `solved` | Получил Accepted на LeetCode |

После ручных изменений метаданных обнови таблицу:

```powershell
python tools/leetcode.py refresh
python tools/leetcode.py check
```

## 4. Сохрани прогресс на GitHub

```powershell
python tools/leetcode.py refresh
git status
git add problems README.md
git commit -m "Solve 0001: Two Sum"
git push
```

Сообщение коммита должно описывать реальную работу: для незавершённой задачи используй, например, `Start 0001: Two Sum` или `Improve 0001: edge cases`.

В этом репозитории локально настроены автор `dormyyy` и адрес `82229543+dormyyy@users.noreply.github.com`, связанный с твоим GitHub-аккаунтом. Общие настройки других репозиториев не меняются. GitHub Actions проверяет файлы, но не создаёт коммиты.

## Папки можно создавать вручную

Создай `problems/0001-two-sum/`, скопируй туда `solution.cpp` и `main.cpp` из `templates/cpp/`, напиши README и добавь `problem.json`:

```json
{
  "id": 1,
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "status": "in-progress",
  "topics": ["array", "hash-table"],
  "solved_on": null
}
```

Для `solved` поле `solved_on` должно содержать дату в формате `YYYY-MM-DD`. Имя папки должно совпадать с номером и `slug`. Номера дополняются нулями минимум до четырёх знаков. Затем запусти `refresh`.

## Проверки репозитория

```powershell
python -m unittest discover -s tests -v
python tools/leetcode.py check
cmake -S . -B build
cmake --build build
```

На GitHub эти проверки выполняются при push и pull request. Если таблица отстала от метаданных, CI попросит запустить `refresh` и закоммитить обновлённый README.
