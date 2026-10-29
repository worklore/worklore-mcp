# Аналитика: регистрация и список предложений

Реализованы все 6 событий из docs/EVENTS.md через `Analytics.capture`. Имена и свойства — как в спецификации; email и телефон не отправляются.

| Событие | Где / когда срабатывает |
|---|---|
| `registration_email_started` | `onChanged` поля email, один раз за визит (флаг `_emailInputFired`) |
| `registration_phone_started` | то же для телефона (`_phoneInputFired`) |
| `loan_amount_changed` | `Slider.onChangeEnd` (когда отпустили), `amount` = округлённое значение |
| `terms_accepted` | при установке галочки (при снятии не отправляется) |
| `registration_continue_tapped` | нажатие Continue, `amount`, `terms` |
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` в `offer_screen.dart`, `offset` = `metrics.pixels` |

## Что пригодилось из заметки коллеги
- Не вешать события на каждый `onChanged`: текстовые поля — один раз за визит по флагу; слайдер — `onChangeEnd`; скролл — `ScrollEndNotification`. Иначе событий десятки на одно действие, а PostHog тарифицируется по их числу.
- Имена и свойства событий не менялись, воронки не затронуты.

Пропущено: проверка через grep и `PostHogConfig.debug` (в проекте не было других capture-вызовов; сборку не запускал), focus-listener (финальные значения полей не нужны).

Примечание: `offers_scrolled` отправляется по окончании каждого жеста прокрутки, а не один раз за визит; если нужно строго один раз — добавить флаг, как у полей. Код не компилировался (Flutter SDK не запускал).
