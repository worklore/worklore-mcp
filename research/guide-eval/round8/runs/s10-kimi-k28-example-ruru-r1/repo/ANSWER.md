# Что сделано

Реализованы все 6 событий из `docs/EVENTS.md` через существующую обёртку
`Analytics.capture()` (`lib/analytics.dart`). Имена событий и свойства — точно
как в спецификации, чтобы существующие дашборды и воронки не сломались. PII
(email, телефон) в свойства не передаётся.

## Экран регистрации (`lib/screens/registration_screen.dart`)

| Событие | Где срабатывает |
|---|---|
| `registration_email_started` | `onChanged` email-поля, один раз за посещение — за флагом `_emailStartedFired` |
| `registration_phone_started` | `onChanged` поля телефона, один раз за посещение — за флагом `_phoneStartedFired` |
| `loan_amount_changed` (`amount`: int) | `onChangeEnd` слайдера — один раз за протягивание, с итоговой суммой |
| `terms_accepted` | `onChanged` чекбокса, когда значение стало `true` (снятие галочки события не шлёт) |
| `registration_continue_tapped` (`amount`: int, `terms`: bool) | `onPressed` кнопки Continue, до навигации на `/offers` |

## Экран предложений (`lib/screens/offer_screen.dart`)

- `offers_scrolled` (`offset`: double) — `OfferScreen` переведён с
  `StatelessWidget` на `StatefulWidget`, список обёрнут в
  `NotificationListener<ScrollNotification>`. Позиция запоминается на
  `ScrollStartNotification`, событие шлётся на `ScrollEndNotification` с
  `offset` = насколько прокрутили за жест (конечная позиция минус начальная).
  События с `offset == 0` (тап без прокрутки) не отправляются. Событие — раз
  за жест прокрутки, а не на каждое обновление скролла.

## Проверка

- `dart format lib/` — прошёл, синтаксис валиден, файлы отформатированы.
- Полный `flutter analyze` и запуск приложения в этой среде выполнить нельзя:
  бинарники `flutter`/`dart` из `~/development/flutter` заблокированы
  (`Operation not permitted`). До пуша стоит прогнать `flutter analyze` и
  ручную проверку на debug-сборке (ввод 20 символов в email → один capture
  `registration_email_started`, протягивание слайдера → одно
  `loan_amount_changed` при отпускании).

## Что пригодилось из заметки коллеги

- **Главный инсайт — ловушка `onChanged`**: текстовое поле шлёт событие на
  каждую клавишу, слайдер — на каждый шаг. Взял решение целиком: флаги
  «один раз за посещение» для текстовых полей (`bool _emailStartedFired`,
  `_phoneStartedFired`), перенос события слайдера в `onChangeEnd`,
  `ScrollEndNotification` вместо обновлений скролла.
- **Правило «не менять имена и свойства событий»** — соблюдено.
- Идея проверки `grep`-ом по `onChanged`/`capture` — фактически выполнена
  при чтении кода (capture нигде не остался «на каждое изменение»).

## Что пропустил из заметки

- **События итогового значения по потере фокуса** (слушатель `FocusNode` при
  `!hasFocus`) — не понадобилось: ни одно событие не требует значения поля,
  спецификация PII это прямо запрещает, а `amount` берётся из состояния
  слайдера, а не из текста.
- **Проверка с `PostHogConfig.debug = true` и PostHog → Activity** — не
  выполнима здесь: бинарник Flutter заблокирован, а ключ в `Analytics.init`
  плейсхолдер (`phc_REPLACE_ME_IN_CI`), отправка во внешний сервис и так
  невозможна. Оставил как рекомендацию для ручной проверки выше.
