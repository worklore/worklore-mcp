# Аналитика: события воронки регистрации

Реализованы все шесть событий из `docs/EVENTS.md`. Отправка идёт только через `Analytics.capture` (`lib/analytics.dart`), ключ и хост не трогались. Имена событий и свойства совпадают со спецификацией. Email и телефон в свойствах не передаются.

## Что изменено

### `lib/screens/registration_screen.dart`

| Событие | Где и когда отправляется | Свойства |
|---|---|---|
| `registration_email_started` | `onChanged` поля email, при первом непустом вводе; один раз за визит на экран | — |
| `registration_phone_started` | `onChanged` поля phone, при первом непустом вводе; один раз за визит на экран | — |
| `loan_amount_changed` | `onChanged` слайдера | `amount` (int) |
| `terms_accepted` | чекбокс переведён в «отмечен» (снятие галочки не шлёт событие) | — |
| `registration_continue_tapped` | нажатие Continue, только когда кнопка активна, до перехода на `/offers` | `amount` (int), `terms` (bool) |

Что добавлено: флаги `_emailStarted` и `_phoneStarted`, методы `_onEmailChanged`, `_onPhoneChanged`, `_onContinue`. Обработчики `onChanged` у полей и `onPressed` кнопки переведены на эти методы.

### `lib/screens/offer_screen.dart`

| Событие | Где и когда отправляется | Свойства |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` вокруг `ListView` — по окончании прокрутки | `offset` (double, `metrics.pixels`) |

## Решения, которые стоит проверить

1. **`offers_scrolled` шлётся по окончании прокрутки**, а не на каждый скролл-нотификейшн. Иначе за одно движение уйдёт десяток событий. Значение `offset` — текущая позиция списка в пикселях в момент остановки.
2. **`loan_amount_changed` шлётся на каждое изменение значения слайдера.** За одно перетаскивание уходит несколько событий (в тесте одно drag-движение дало три). Если это слишком шумно для бесплатного тарифа PostHog, вариант — перенести отправку в `onChangeEnd`. Тогда будет одно событие на жест, но без промежуточных значений.
3. **`*_started` — один раз за визит на экран.** Флаг сбрасывается при новом открытии экрана. Если нужна привязка к сессии, а не к экрану, это другое решение.
4. **`registration_continue_tapped` не шлётся, если кнопка неактивна** (нет terms, некорректный email или телефон). Это соответствует «User tapped Continue»: нажатием считаем только активную кнопку.

## Проверка

- `dart format --set-exit-if-changed lib` — без изменений.
- `flutter analyze` на исходном `analysis_options.yaml` — «No issues found!».
- Временный виджет-тест (перехват вызовов канала `posthog_flutter`) подтвердил, что при сценарии «ввод email → ввод телефона → две галочки на terms → движение слайдера → Continue → скролл списка» уходят:
  - `registration_email_started` (один раз, несмотря на два ввода);
  - `registration_phone_started` (один раз);
  - `terms_accepted` ×2 (поставили, сняли, поставили);
  - `loan_amount_changed` с `amount` (несколько раз за drag);
  - `registration_continue_tapped` с `amount` и `terms: true`;
  - `offers_scrolled` с `offset`.
  Тест удалён, так как в проекте нет каталога `test/` и я не добавлял его в репозиторий.

Не проверено: отправка в реальный PostHog (сеть и ключ — заглушка `phc_REPLACE_ME_IN_CI`), работа на устройстве.

## Что не менялось

- `lib/analytics.dart`, `lib/main.dart`, `docs/EVENTS.md`, `pubspec.yaml`.
- Коммиты не создавались, ничего не публиковалось и не отправлялось.
