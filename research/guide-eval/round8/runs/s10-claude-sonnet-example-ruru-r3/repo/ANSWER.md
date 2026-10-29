# Аналитика: регистрация и список предложений

Реализованы все 6 событий из docs/EVENTS.md через `Analytics.capture`. Имена и свойства совпадают со спецификацией, email и телефон не отправляются.

| Событие | Где / когда срабатывает |
|---|---|
| `registration_email_started` | `onChanged` поля email, один раз за посещение экрана (флаг `_emailStartedFired`) |
| `registration_phone_started` | то же для телефона (`_phoneStartedFired`) |
| `loan_amount_changed` | `Slider.onChangeEnd`, `amount` = округлённое значение; один раз за протягивание |
| `terms_accepted` | при установке галочки (только `true`) |
| `registration_continue_tapped` | нажатие Continue, `amount` (int), `terms` (bool) |
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>`, `offset` = `metrics.pixels`; один раз за посещение (флаг `_scrolledFired`). `OfferScreen` стал `StatefulWidget` |

## Что пригодилось из заметки коллеги
- Флаг «один раз за посещение» для текстовых полей: `onChanged` срабатывает на каждое нажатие клавиши, а платформа тарифицирует события.
- Слайдер: событие в `onChangeEnd`, а не в `onChanged`.
- Скролл: `ScrollEndNotification` вместо обновлений скролла.
- Имена и свойства событий не менялись.

Пропущено: события по потере фокуса (`FocusNode`) — итоговые значения спецификации не нужны; дебаунс и `PostHogConfig.debug` для проверки.

Не запускалось: Flutter/Dart-проверок (analyze, сборка, запуск) не выполнял.
