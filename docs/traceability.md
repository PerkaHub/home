# Матрица прослеживаемости

Матрица связывает требования с проектом и кодом ЛР 3. Для частичной реализации указан объём проверки. ADR-0001–0005 приняты для текущей спецификации.

| Требование | Приоритет / источник | Событие / агрегат | ADR | Контейнер / таблицы | Операция | План проверки | Код / состояние |
|---|---|---|---|---|---|---|---|
| FR-01 | Must / P1–P3, истории US | Привязка подтверждена / Invitation | 0004, 0002 | api/db; invitation, membership, account | POST /v1/memberships | AC-01.1–4, ЛР 5 | — / спроектировано |
| FR-02 | Must / P1–P3, истории US | Начисление опубликовано / Charge | 0003, 0002 | api сейчас; charge, charge_line в ЛР 4А | POST /v1/charges/{id}/publications | AC-02.1–4 в `tests/test_charges_api.py`, без ролей и БД | `src/domprozrachno/modules/billing`, `api/charges.py` / учебный сценарий |
| FR-03 | Must / P1–P3, истории US | Отчёт опубликован / ExpenseReport | 0003, 0002 | api/db; expense_report, expense_item | POST /v1/expense-reports/{id}/publications | AC-03.1–4, ЛР 5 | — / спроектировано |
| FR-04 | Must / P1–P3, истории US | Условия оплаты рассчитаны / PaymentQuote | 0005, 0002 | api/db; payment_quote | POST /v1/charges/{id}/payment-quotes | AC-04.1–4, ЛР 5 | — / спроектировано |
| FR-05 | Must / P1–P3, истории US | Платёж подтверждён / PaymentAttempt | 0005, 0002 | api/db; payment_attempt, payment_event, charge | POST /v1/payment-attempts; POST /v1/provider-events | AC-05.1–8, ЛР 5 | — / спроектировано |
| FR-06 | Must / P1–P3, истории US | Чтение не создаёт событие / PaymentAttempt | 0004, 0002 | api/db; payment_attempt | GET /v1/accounts/{id}/payment-attempts | AC-06.1–4, ЛР 5 | — / спроектировано |
| BR-01 | Should / Заказчик | — / сквозное | 0003 | web | — | Оценка 2/5 → цель 4/5 завершения | — / план |
| BR-02 | Should / Заказчик | — / сквозное | 0003 | web | — | Оценка базы 300 с → цель ≤120 с | — / план |
| NFR-01 | Should / P1 | — / сквозное | 0002/0005 | api/db | — | 20 RPS, p95 ≤500 мс | — / план |
| NFR-02 | Must / P3 | — / сквозное | 0005 | api/worker/db | — | 100 параллельных повторов | — / план |
| NFR-03 | Should / Эксплуатация | — / сквозное | 0003 | db | — | Восстановление dump ≤30 мин. | — / план |
| NFR-04 | Must / P1 | — / сквозное | 0004 | api/db | — | Матрица 3 ролей / 2 домов | — / план |
| NFR-05 | Should / Эксплуатация | — / сквозное | 0003/0004 | api/worker | — | `tests/test_system_api.py`, проверка журнала публикации. Платёжные сценарии и worker — следующий этап | `src/domprozrachno/logging.py`, `api/middleware.py` / локальный журнал API |
| NFR-06 | Should / Разработка | — / сквозное | 0003 | api | — | CI `boundaries`, включая отрицательные проверки | `scripts/check_architecture.py` / действует для domain и application |
| NFR-07 | Must / Преподаватель | — / сквозное | 0001 | CI | — | Прогон документации и диаграмм | `scripts/check_docs.py`, `scripts/render-diagrams.mjs`, `.github/workflows/ci.yml` / действует |
| NFR-08 | Could / Эксплуатация | — / сквозное | 0005 | api/db | — | 100000 попыток, p95 ≤1 с | — / план |
| NFR-09 | Must / Эксплуатация | — / сквозное | 0002, 0003 | api | GET /health, GET /version | `tests/test_system_api.py`, smoke-тест Compose с остановкой db | `src/domprozrachno/api/system.py` / реализовано |
| NFR-10 | Must / Разработка | — / сквозное | 0002 | CI | — | pytest с порогом 70% и тайм-аутом 60 с | `pyproject.toml`, `.github/workflows/ci.yml` / действует |

Обратная проверка ЛР 3. Служебные обработчики следуют из NFR-09. Создание, публикация и чтение начисления следуют из FR-02 и покрывают AC-02.1–4 в рамках одного синтетического счёта. Все Must и Should включены. Порядок обновления: требование → агрегат → ADR → модель/ресурс → план теста; при появлении кода добавить фактический путь и результат проверки.
