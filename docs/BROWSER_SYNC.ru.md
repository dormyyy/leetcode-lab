# Подключение Accepted из Opera GX

Интеграция репозитория подготовлена для **AlgoVault**. Само расширение надо установить и авторизовать в Opera GX; наличие этих файлов не означает, что браузер уже подключён.

## 1. Установи AlgoVault

Открой [AlgoVault в Chrome Web Store](https://chromewebstore.google.com/detail/algovault/glpcihnambokpffjbhmlnbcmpbcdhihb) **в Opera GX** и установи расширение. Проверенная карточка магазина: AlgoVault, автор Vikas Kushwaha, версия 0.1.1.

Opera поддерживает расширения Chrome Web Store. Если кнопка установки отсутствует, используй подсказки самого браузера; [справка Opera](https://help.opera.com/en/faq/). Установка в браузер Codex не подключит твой профиль Opera.

## 2. Создай токен от dormyyy

Войди на GitHub именно как `dormyyy`. Открой [форму fine-grained token с заполненными основными полями](https://github.com/settings/personal-access-tokens/new?name=LeetCode%20Lab%20%28AlgoVault%29&target_name=dormyyy&expires_in=90&contents=write).

Выставь:

| Поле | Значение |
| --- | --- |
| Resource owner | `dormyyy` |
| Repository access | **Only select repositories** |
| Selected repository | **leetcode-lab** |
| Repository permission | **Contents: Read and write** |
| Expiration | 90 дней или выбранный тобой срок |

`Metadata: Read-only` GitHub добавляет автоматически. Другие права не нужны. Создай токен, скопируй его и вставь **только в настройки AlgoVault**. Токен не нужен в чате, в `leetcode.json`, в импортируемом JSON или в репозитории.

Источники: [права GitHub](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens), [исходники и настройка AlgoVault](https://github.com/vikas-kushwaha-dev/algovault-extension).

## 3. Импортируй готовые настройки

Открой AlgoVault → **Import settings** и выбери:

```text
D:\Study\leetcode\docs\algovault-settings.json
```

Файл не содержит токена. Настройки после импорта:

| Поле | Значение |
| --- | --- |
| Owner | `dormyyy` |
| Repository | `leetcode-lab` |
| Branch | `main` |
| Folder template | `browser-sync/{number}-{slug}` |
| File template | `solution{ext}` |

Вставь токен и нажми **Save / Test connection**. Разреши запрос AlgoVault к `api.github.com`, если браузер его покажет. Ожидаемое сообщение: **Connected. AlgoVault can write to the selected repository.**

Затем обнови вкладку LeetCode. Ты должен быть залогинен в своём аккаунте `dormyyy`.

## Что произойдёт после Accepted

1. AlgoVault читает принятую отправку через текущую сессию LeetCode в браузере.
2. Оригинальный код появляется в `browser-sync/0002-add-two-numbers/solution.cpp` одним коммитом от владельца токена.
3. GitHub Actions создаёт или обновляет задачу в `problems/`, сохраняет оригиналы в её папке `accepted/`, отмечает Accepted и обновляет README.
4. Для CLion C++ starter заменяется принятым кодом со стандартными includes. Последующие версии автоматически обновляют основной файл, пока ты не изменил его самостоятельно.
5. Если в `solution.cpp` уже есть твои отличающиеся правки, они сохраняются. Принятый вариант всё равно доступен в `accepted/`; его путь есть в `problem.json` → `browser_sync.latest_cpp`.

README задачи и заметки не перезаписываются. Разные решения сохраняются отдельно. Python и другие языки тоже архивируются, но не заменяют C++-файл. Для новой задачи `solved_on` берётся из даты первого импорта, если прежняя дата не известна; это отмечено в `solved_on_source`.

Чтобы новые файлы появились **на компьютере**, выполни:

```powershell
git pull
```

Расширение пишет на GitHub, а не в локальный каталог. Если есть незакоммиченные правки и Git сообщает конфликт, сохрани их перед обновлением. После pull задачи доступны в CLion.

## Авторство

AlgoVault создаёт Git-коммиты без переопределения автора: GitHub использует пользователя токена как author, а committer наследует author. Поэтому токен должен принадлежать **dormyyy**. [Правила GitHub API](https://docs.github.com/en/rest/git/commits#create-a-commit).

Импортирующие и обновляющие счётчик GitHub Actions явно используют:

```text
dormyyy <82229543+dormyyy@users.noreply.github.com>
```

CI дополнительно проверяет `author.login` и `committer.login` коммита через GitHub API и сообщает ошибку, если это не `dormyyy`.

## Первая проверка

После твоего следующего настоящего Accepted проверь зелёный статус AlgoVault и появление коммита. Затем открой [Actions](https://github.com/dormyyy/leetcode-lab/actions) и папку задачи. Без настоящей отправки нельзя подтвердить весь путь от сессии Opera до репозитория; искусственные решения не отправляются ради проверки настройки.

Репозиторная часть проверена тестами на сохранение кода, заметок, альтернативных версий, повторного импорта и неправильных номеров задач. Если метаданные LeetCode временно недоступны, оригинальный принятый код останется в `browser-sync/`, а импорт можно повторить запуском workflow.
