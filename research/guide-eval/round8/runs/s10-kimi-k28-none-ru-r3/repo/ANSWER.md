# Ответ

Реализованы все 6 событий из `docs/EVENTS.md` через существующую обёртку
`Analytics.capture` (`lib/analytics.dart`). Изменены файлы:

## `lib/screens/registration_screen.dart`

| Событие | Где вызывается | Параметры |
|---|---|---|
| `registration_email_started` | `_onEmailChanged` — один раз, при первом непустом вводе в поле Email | — |
| `registration_phone_started` | `_onPhoneChanged` — один раз, при первом непустом вводе в поле Phone | — |
| `loan_amount_changed` | `onChangeEnd` слайдера (жест завершён, сумма выбрана) | `amount` (int, округлённое значение) |
| `terms_accepted` | `_onTermsChanged` — только при установке галочки | — |
| `registration_continue_tapped` | `_onContinue` — по нажатию Continue, перед навигацией | `amount` (int), `terms` (bool) |

## `lib/screens/offer_screen.dart`

| Событие | Где вызывается | Параметры |
|---|---|---|
| `offers_scrolled` | `_onScroll` — слушатель `ScrollController` списка | `offset` (double, текущий пиксельный offset) |

Экран переведён с `StatelessWidget` на `StatefulWidget`, чтобы держать
`ScrollController`.

## Принятые решения

- **Email/phone как параметры не отправляются** (PII) — в событиях уходят
  только `amount` и `terms`, как требуют notes в доке.
- **`registration_*_started` — один раз на сессию экрана**: событие
  срабатывает при первом непустом вводе (флаги `_emailStarted` /
  `_phoneStarted`), повторный набор в том же поле не плодит события.
- **`loan_amount_changed` на `onChangeEnd`, а не `onChanged`**: `onChanged`
  шлёт десятки событий за один drag, а по доке `amount` — «выбранная сумма».
  Так одно движение слайдера = одно событие с итоговым значением.
- **`terms_accepted`** срабатывает только при установке галочки; снятие
  галочки события не шлёт.
- **`offers_scrolled` троттлится до 1 события в секунду**, иначе скролл
  генерирует событие на каждый кадр (~60/с). `offset` берётся текущий
  из `_scrollController.offset`.
- Все вызовы обёрнуты в `unawaited(...)` (dart:async) — fire-and-forget,
  без блокировки UI и без линта `unawaited_futures` из flutter_lints.
- Автотрекинг экранов не трогал — `PosthogObserver` в `main.dart` уже
  покрывает screen views (по доке отдельное событие не нужно).

## Проверка

`flutter analyze` / `dart analyze` запустить не удалось — песочница сессии
блокирует исполнение бинарников вне рабочей директории
(`Operation not permitted` для `~/development/flutter/bin/*`). Изменения
проверены ревью кода; синтаксис соответствует Dart 3.5 / Flutter stable,
имена событий совпадают с таблицей в `docs/EVENTS.md` точь-в-точь
(snake_case). Рекомендую прогнать `flutter analyze` локально.
