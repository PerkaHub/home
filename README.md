# ДомПрозрачно

Учебная веб-платформа: доступ жителя к счёту, прозрачные начисления и расходы дома, тестовая оплата. Команда: Белянский Глеб, Опекин Егор, Рогачев Егор.

## Состояние

ЛР 1 — продуктовые документы. ЛР 2 — проектирование без кода приложения. Сервер пока не запускается; все данные будущей демонстрации синтетические. Платёжный sandbox ещё предстоит выбрать и проверить.

## Документы

- [Требования и критерии](docs/requirements.md), [матрица](docs/traceability.md).
- [Модель событий](docs/domain/event-storming.md), [агрегаты](docs/domain/aggregates.md), [глоссарий](docs/domain/ubiquitous-language.md).
- [Обзор архитектуры](docs/architecture/overview.md), [диаграммы](docs/architecture/README.md), [ADR](docs/adr/README.md), [ресурсы API](docs/api/resources.md).
- [Карта историй](docs/user-story-map.md), [путь жителя](docs/customer-journey-map.md), [план](docs/roadmap.md), [процесс](docs/process.md).
- [Проверки и открытые пункты](docs/verification.md), [журнал](docs/CHANGELOG.md).

## Локальная проверка

Нужны Python 3.11+ и Node.js 22+ с npm. Из корня репозитория:

```sh
python scripts/check_docs.py
npm ci
npm run diagrams
python scripts/check_docs.py --self-test
```

SVG создаются в build/diagrams и не включаются в Git. npm ci требует сеть при первой установке; Chromium загружается установщиком Puppeteer. CI выполняет те же проверки. Изменения — через небольшую ветку и содержательное ревью по [CONTRIBUTING](CONTRIBUTING.md).
