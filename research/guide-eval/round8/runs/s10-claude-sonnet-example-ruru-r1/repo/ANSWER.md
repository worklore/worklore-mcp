# Что сделано

Все 6 событий из docs/EVENTS.md подключены через `Analytics.capture`. Имена и свойства точно по спецификации, email и телефон не передаются.

| Событие | Где и когда |
|---|---|
| `registration_email_started` | `registration_screen.dart`, `onChanged` поля email, один раз за посещение (флаг `_emailStartedFired`) |
| `registration_phone_started` | то же для телефона (`_phoneStartedFired`) |
| `loan_amount_changed` | `Slider.onChangeEnd`, `amount` = округлённая сумма |
| `terms_accepted` | при установке галочки (снятие не отправляется) |
| `registration_continue_tapped` | тап Continue, `amount` и `terms` |
| `offers_scrolled` | `offer_screen.dart`: `NotificationListener<ScrollEndNotification>`, `offset` = `metrics.pixels`, один раз за посещение |

`OfferScreen` стал `StatefulWidget` ради флага.

# Что пригодилось из заметки коллеги
- Пригодилось всё по существу: события на `onChanged` текстовых полей и слайдера слали бы событие на каждое нажатие/шаг. Поэтому текстовые поля — флаг «один раз», слайдер — `onChangeEnd`, скролл — `ScrollEndNotification`.
- Не пригодилось: `FocusNode`/потеря фокуса (итоговые значения не нужны, а email/телефон нельзя отправлять), grep-проверка (существующих capture в коде не было), проверка через `PostHogConfig.debug` (не запускалось).

# Решения и допущения
- «Один раз» для `offers_scrolled` и `*_started` — за посещение экрана, т.к. воронка требует только факта. Если нужно по каждому окончанию скролла — уберите флаг.
- `offers_scrolled` не шлётся при `pixels == 0` (нет реального скролла).
- `dart format` выполнен; `flutter analyze` и запуск приложения не делались (пакеты не установлены).
