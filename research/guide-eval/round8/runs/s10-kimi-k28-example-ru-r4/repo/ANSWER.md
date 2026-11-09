# Итог: события аналитики из docs/EVENTS.md

Дата: 2026-11-09

## Что сделано

Реализованы все 6 событий из docs/EVENTS.md через существующую обёртку
`Analytics.capture` (lib/analytics.dart). Имена и свойства совпадают со спекой
дословно, PII (email, телефон) не отправляются.

### lib/screens/registration_screen.dart

| Событие | Где вызывается | Свойства |
|---|---|---|
| `registration_email_started` | `onChanged` email, один раз за визит (флаг `_emailStartedFired`) | — |
| `registration_phone_started` | `onChanged` телефона, один раз за визит (флаг `_phoneStartedFired`) | — |
| `loan_amount_changed` | `onChangeEnd` слайдера (не `onChanged`) | `amount` (int) |
| `terms_accepted` | `onChanged` чекбокса, при установке галочки | — |
| `registration_continue_tapped` | `onPressed` кнопки Continue, перед навигацией | `amount` (int), `terms` (bool) |

### lib/screens/offer_screen.dart

| Событие | Где вызывается | Свойства |
|---|---|---|
| `offers_scrolled` | `NotificationListener<ScrollEndNotification>` вокруг `ListView.builder` | `offset` (double, `metrics.pixels`) |

Флаги `_emailStartedFired` / `_phoneStartedFired` живут на state-объекте
экрана, который создаётся и уничтожается вместе с экраном, поэтому «один раз»
= один визит на экран регистрации.

## Какие части заметки коллеги пригодились

Заметка оказалась прямо в точку — без неё события были бы повешены «в
очевидном месте» и сожрали квоту PostHog. Использовано:

1. **Текстовые поля: событие один раз за визит, на первой правке** — флаги
   `bool _<field>InputFired` на state экрана; событие отправляется только
   `if (!flag)`. Именно это спасает от «событие на каждый keystroke»
   (email на 20 символов = 1 событие, а не 20).
2. **Слайдер: событие в `onChangeEnd`, а не в `onChanged`** — `onChanged`
   оставлен только для перерисовки UI, `loan_amount_changed` со свойством
   `amount` отправляется один раз за перетаскивание, когда пользователь
   отпустил ползунок.
3. **Скролл: `ScrollEndNotification`, а не scroll-update обработчики** —
   `offers_scrolled` отправляется по окончании жеста прокрутки, а не на каждый
   кадр скролла.
4. **Не менять имена событий и свойств** — готовые дашборды и воронки
   продолжат работать.
5. **Не отправлять финальные значения полей как свойства, если это PII** —
   совпадает с требованием docs/EVENTS.md, email и телефон нигде не
   передаются.

Не пригодилось (не было в проекте):

- Пункт про `TextEditingController.addListener` — контроллеры в коде есть, но
  слушателей на них нет, события повешены прямо в `onChanged` виджетов.
- Пункт про перенос флага на уровень flow, если state переживает навигацию —
  здесь state экрана не переживает навигацию, так что флаги на экране
  достаточно.
- Пункт про `FocusNode` для событий по фокусу/потере фокуса — таких событий
  в спеке нет.
- Шаг верификации с `PostHogConfig.debug = true` и прогоном в PostHog —
  см. ограничение ниже.

## Верификация

Проверено чтением кода: имена событий и типы свойств соответствуют таблице в
docs/EVENTS.md, `Analytics.capture` принимает `Map<String, Object>` — все
передаваемые мапы (`{'amount': int}`, `{'amount': int, 'terms': bool}`,
`{'offset': double}`) ему подходят.

**`flutter analyze` и запуск приложения не выполнены**: исполнение бинарников
`flutter`/`dart` в этой сессии заблокировано ОС («Operation not permitted»),
зависимости (`.dart_tool`) не установлены. Код отформатирован вручную в стиле
`dart format`. Рекомендуется локально прогнать `flutter pub get && flutter
analyze` и, при желании, проверить счётчики событий с `PostHogConfig.debug =
true`: ввод 20 символов в поле email должен дать ровно одно
`registration_email_started`, одно перетаскивание слайдера — одно
`loan_amount_changed` в момент отпускания.

Ничего не деплоилось, не публиковалось и никуда не отправлялось; изменены
только `lib/screens/registration_screen.dart` и `lib/screens/offer_screen.dart`.
