# Что сделано

Реализованы все события из `docs/EVENTS.md` через существующую обёртку `Analytics.capture`.

## Экран регистрации

В `lib/screens/registration_screen.dart` добавлены:

- `registration_email_started` — один раз за показ экрана при первом изменении email;
- `registration_phone_started` — один раз за показ экрана при первом изменении телефона;
- `loan_amount_changed` — в `onChangeEnd` слайдера, с итоговым целочисленным свойством `amount`;
- `terms_accepted` — при установке флажка согласия, без события при его снятии;
- `registration_continue_tapped` — при нажатии доступной кнопки Continue, со свойствами `amount` (int) и `terms` (bool), перед переходом к предложениям.

Email и телефон в свойства событий не передаются.

## Экран предложений

В `lib/screens/offer_screen.dart` список обёрнут в `NotificationListener<ScrollEndNotification>`. После завершения прокрутки отправляется `offers_scrolled` со свойством `offset` (double), равным `notification.metrics.pixels`.

## Что пригодилось из заметки коллеги

Пригодились рекомендации ограничивать частоту событий, сохраняя их имена и свойства:

- флаги `_emailInputFired` и `_phoneInputFired` обеспечивают одно событие на первое редактирование каждого поля за показ экрана вместо события на каждое нажатие клавиши;
- событие слайдера вынесено из `onChanged` в `onChangeEnd`, поэтому `onChanged` только обновляет UI;
- для списка используется `ScrollEndNotification`, а не события каждого обновления прокрутки.

Рекомендации по FocusNode и передаче итогового значения полей не применялись: спецификация требует только факт начала ввода и запрещает передавать email и телефон.

## Проверка

`git diff --check` выполнен успешно. Запустить `dart format` и `flutter analyze` не удалось: macOS возвращает `Operation not permitted` для обоих исполняемых файлов Flutter SDK. Тестов в проекте нет.
