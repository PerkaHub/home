# ДомПрозрачно

«ДомПрозрачно» помогает жителям проверять начисления и расходы дома. Команда — Белянский Глеб, Опекин Егор и Рогачев Егор.

API на FastAPI позволяет создать черновик, опубликовать начисление и прочитать его по ID. Маршруты `/health` и `/version` показывают состояние и версию сервиса.

## Быстрый запуск

Нужны Git и [uv](https://docs.astral.sh/uv/getting-started/installation/). Для запуска в контейнерах нужен запущенный Docker с Compose v2 или новее. Все команды выполняются из корня репозитория.

```sh
git clone --branch lab3 https://github.com/PerkaHub/home.git
cd home
uv python install
uv sync --locked
```

Скопируйте `.env.example` в `.env` командой `Copy-Item .env.example .env` в PowerShell или `cp .env.example .env` в bash. Затем запустите сервер.

```sh
uv run --locked python -m domprozrachno
```

В другом терминале проверьте [живость](http://127.0.0.1:8080/health) и [версию](http://127.0.0.1:8080/version). `/health` отвечает HTTP 200 и `{"status":"ok"}`. Остановите локальный сервер перед запуском Compose на том же порту.

### Docker Compose

```sh
docker compose up -d --build --wait
docker compose ps
docker compose logs -f api
```

API доступен на `127.0.0.1:8080`. Compose дожидается PostgreSQL, данные базы сохраняются в томе `pgdata`. Для остановки выполните `docker compose down`.

### Настройки

| Переменная | Значение |
|---|---|
| `DATABASE_URL` | Обязательный адрес PostgreSQL. Compose передаёт адрес базы из своей сети |
| `HOST` | Адрес привязки API, локально `127.0.0.1`. В контейнере `0.0.0.0` |
| `PORT` | Порт 1–65535, по умолчанию 8080 |
| `APP_ENV` | `development`, `test` или `production`. Демонстрационный счёт доступен в `development` и `test` |
| `APP_VERSION` | Версия, которую возвращает `/version`, по умолчанию `0.8.0` |
| `LOG_LEVEL` | `debug`, `info`, `warning` или `error` |

Переменные окружения имеют приоритет над `.env`. Опечатка в ключе `.env` останавливает запуск. Для незнакомых переменных самого процесса это правило не действует. Журнал доступен в stdout, по одному JSON-объекту на строку. Переданный `X-Request-Id` принимается, если содержит 1–64 латинских буквы, цифры, дефисы или подчёркивания. В остальных случаях сервер создаёт UUID.

## Демонстрация М08

1. В [Swagger UI](http://127.0.0.1:8080/docs) откройте `POST /v1/accounts/{account_id}/charges`. Укажите счёт `00000000-0000-4000-8000-000000000001` и отправьте черновик.
2. Скопируйте `id` из ответа 201. Подставьте его в `POST /v1/charges/{charge_id}/publications`. Ответ 201 содержит статус `published`, дату публикации, строки и итог.
3. Откройте `GET /v1/charges/{charge_id}` с тем же ID. Повторная публикация и публикация второго начисления за тот же месяц дают 409.
4. Для ответа 422 создайте черновик с периодом `2026-13` или с итогом, отличным от суммы строк.

```json
{
  "period": "2026-11",
  "amount_minor": 30000,
  "lines": [
    {"service": "Отопление", "basis": "Показания счётчика", "amount_minor": 10000},
    {"service": "Вода", "basis": "Показания счётчика", "amount_minor": 20000}
  ]
}
```

Начисления хранятся в памяти API. После перезапуска начните демонстрацию с нового черновика.

## Проверки

```sh
uv run --locked pytest --cov
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src tests
uv run --locked python scripts/check_architecture.py boundaries --self-test
uv run --locked python scripts/check_architecture.py language --self-test
```

Для проверки документов и диаграмм дополнительно нужны Node.js 22+ и npm. SVG создаются в `build/diagrams`.

```sh
uv run --locked python scripts/check_docs.py
uv run --locked python scripts/check_docs.py --self-test
uv run --locked python scripts/check_payment_protocol.py
npm ci
npm run diagrams
npm run test:diagrams
```

## Документы

- [Лабораторная работа № 3](docs/lab-m07-m08.md) и [отчёт о рефакторинге](docs/refactoring-notes.md).
- [Требования](docs/requirements.md), [матрица прослеживаемости](docs/traceability.md), [агрегаты](docs/domain/aggregates.md) и [глоссарий](docs/domain/ubiquitous-language.md).
- [Архитектура](docs/architecture/overview.md), [диаграммы](docs/architecture/README.md), [ADR](docs/adr/README.md) и [ресурсы API](docs/api/resources.md).
- [Материалы ЛР 2](docs/verification.md), [процесс](docs/process.md) и [журнал изменений](docs/CHANGELOG.md).
