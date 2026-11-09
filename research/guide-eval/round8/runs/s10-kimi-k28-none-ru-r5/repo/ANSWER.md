# Что сделано

Реализованы все 6 событий из `docs/EVENTS.md` на экранах регистрации
(`lib/screens/registration_screen.dart`) и списка предложений
(`lib/screens/offer_screen.dart`) через существующую обёртку
`Analytics.capture` (`lib/analytics.dart`). Показ экранов по-прежнему
трекается автоматически через `PosthogObserver`, отдельные события для
экранов не добавлялись (как указано в notes).

## События на экране регистрации

- `registration_email_started` — отправляется один раз, когда пользователь
  впервые вводит непустой текст в поле Email (флаг `_emailStartedSent`).
  Значение email в свойствах не передаётся (PII).
- `registration_phone_started` — аналогично для поля Phone (флаг
  `_phoneStartedSent`), номер не передаётся.
- `loan_amount_changed` — отправляется в `onChangeEnd` слайдера (по
  окончании жеста, со значением, которое пользователь выбрал), свойство
  `amount` (int, округлённое значение). Отправка по `onChangeEnd`, а не
  `onChanged`, чтобы не спамить событием на каждый кадр перетаскивания.
- `terms_accepted` — отправляется при установке галочки условий.
- `registration_continue_tapped` — отправляется по нажатию Continue до
  навигации, свойства `amount` (int) и `terms` (bool). Кнопка активна
  только когда оба условия выполнены, поэтому `terms` всегда `true`.

## События на экране предложений

- `offers_scrolled` — экран конвертирован из `StatelessWidget` в
  `StatefulWidget`; добавлен `NotificationListener<ScrollNotification>`.
  Во время скролла запоминается максимальный `pixels` offset, после
  окончания жеста (`ScrollEndNotification`) отправляется событие со
  свойством `offset` (double) — «насколько далеко проскроллил». Одно
  событие на жест вместо потока событий на каждый кадр; жест без
  фактического скролла событие не порождает.

## Примечания

- Изменены только два файла экранов; `analytics.dart`, `main.dart`,
  `pubspec.yaml` не трогал — API обёртки подошёл как есть.
- Имена событий snake_case совпадают с таблицей в `docs/EVENTS.md` точно.
- PII (email, телефон) никуда не отправляются как свойства.

## Проверка

`flutter analyze` не запускался: в проекте нет `.dart_tool`/`.dart_spec.lock`
(зависимости не подтянуты), а `pub get` потребовал бы сетевого обращения,
что запрещено правилами задачи; кроме того, песочница окружения блокирует
исполнение локального Flutter SDK (Operation not permitted). Код проверен
вручную: синтаксис, импорты (`../analytics.dart` относительно `lib/screens/`),
типы свойств (`int`, `bool`, `double`) соответствуют сигнатуре
`Analytics.capture(String, [Map<String, Object>?])`.
