# Аналитика: события из docs/EVENTS.md

## Что сделано

Все шесть событий из `docs/EVENTS.md` подключены через `Analytics.capture`.
Имена событий и свойства не менялись.

**`lib/screens/registration_screen.dart`**

| Событие | Где срабатывает | Свойства |
|---|---|---|
| `registration_email_started` | `onChanged` поля email, один раз за посещение экрана (флаг `_emailStartedFired`) | — |
| `registration_phone_started` | `onChanged` поля phone, один раз за посещение (флаг `_phoneStartedFired`) | — |
| `loan_amount_changed` | `Slider.onChangeEnd`, один раз за протягивание | `amount` (int) |
| `terms_accepted` | `CheckboxListTile.onChanged`, когда значение стало `true` | — |
| `registration_continue_tapped` | `onPressed` кнопки Continue, только когда она активна | `amount` (int), `terms` (bool) |

**`lib/screens/offer_screen.dart`**

| Событие | Где срабатывает | Свойства |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` вокруг `ListView` | `offset` (double, `metrics.pixels`) |

`onChanged` у `Slider` оставлен только для обновления UI. Email и телефон в
свойства не попадают (PII).

## Проверка

- `dart format --set-exit-if-changed lib/` — после форматирования чисто.
- `flutter analyze lib` — `No issues found!`
- Реальную отправку в PostHog не проверял: в `lib/analytics.dart` стоит
  заглушка ключа `phc_REPLACE_ME_IN_CI`, и на устройстве я не запускал.
  Проверка по логам описана ниже.

## Что взял из заметки коллеги

Пригодилось:
- Текстовые поля: флаг «один раз за посещение» в состоянии экрана. Состояние
  пересоздаётся при каждом переходе на экран, поэтому флаг сбрасывается за
  посещение.
- Слайдер: событие перенесено из `onChanged` в `onChangeEnd`, чтобы не
  отправлять по событию на каждый шаг.
- Скролл: `ScrollEndNotification` вместо `ScrollUpdateNotification`.

Не пригодилось:
- Шаги про `FocusNode` и событие при потере фокуса. В `EVENTS.md` нет события,
  которому нужно итоговое значение поля, а `onChanged` для `*_started` уже
  даёт нужный «один раз».
- Шаг про `PostHogConfig.debug = true` и проверку по PostHog → Activity. Я это
  не запускал, см. ниже.
- Сама проверка на «касается ли это вас» — код уже известен, grep не нужен.

## Решения, которые стоит проверить

- `terms_accepted` срабатывает при каждом включении чекбокса, включая повторное
  после снятия. В спецификации это не оговорено.
- `loan_amount_changed` срабатывает и на тап по слайдеру без протягивания
  (`onChangeEnd` вызывается и тогда).
- `offers_scrolled.offset` — абсолютная позиция `metrics.pixels` в момент
  окончания скролла, а не дельта. Если нужна дельта, это другое значение.
- `ScrollEndNotification` может прийти без реального движения пользователя
  (например, после короткого fling). Я не фильтровал такие случаи.

## Не сделано

- Не коммитил и не отправлял ничего в PostHog.
- `README.md` в строке «the screens do not send any of them yet» теперь
  неверен. Не трогал, так как это документация вне задания.
- Ручную проверку на устройстве (debug-лог, одно событие на 20 символов,
  одно событие на протягивание слайдера) не выполнял. Её стоит сделать
  перед релизом.
