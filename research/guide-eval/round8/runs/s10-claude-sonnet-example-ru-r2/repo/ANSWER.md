# Analytics events

Все 6 событий из `docs/EVENTS.md` отправляются через `Analytics.capture`, имена и свойства как в спецификации. Email и телефон не передаются.

**Регистрация** (`registration_screen.dart`)
- `registration_email_started` / `registration_phone_started`: один раз за визит экрана, при первой правке (флаги `_emailStartedFired`, `_phoneStartedFired`), а не на каждое нажатие клавиши.
- `loan_amount_changed` (`amount`): в `onChangeEnd` слайдера, то есть один раз за перетаскивание. `onChanged` только обновляет UI.
- `terms_accepted`: только когда галочка поставлена.
- `registration_continue_tapped` (`amount`, `terms`): при нажатии Continue.

**Список предложений** (`offer_screen.dart`)
- Экран стал `StatefulWidget`. `offers_scrolled` (`offset`) отправляется из `NotificationListener<ScrollEndNotification>`, один раз за визит, при окончании первой прокрутки. Offset — позиция на конец первой прокрутки.

**Что пригодилось из заметки коллеги:** флаг «один раз» для текстовых полей, `onChangeEnd` для слайдера, `ScrollEndNotification` для скролла, и то, что имена и свойства событий не меняются. Это нужно из-за бесплатного тарифа PostHog (в README).
**Пропущено:** фокус-слушатели (событий с финальным значением нет), `PostHogConfig.debug`, grep-проверка (в коде не было других вызовов).

Проверено только `dart format` (прошёл). Сборка и `flutter analyze` не запускались: пакеты не разрешены (`flutter_lints`).
