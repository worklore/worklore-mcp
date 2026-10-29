# Аналитика: события из docs/EVENTS.md

Все 6 событий отправляются через `Analytics.capture` (`lib/analytics.dart`). Имена событий совпадают со спецификацией символ в символ.

| Событие | Где / когда отправляется | Свойства |
|---|---|---|
| `registration_email_started` | `registration_screen.dart`, первый непустой ввод в поле Email | — |
| `registration_phone_started` | `registration_screen.dart`, первый непустой ввод в поле Phone | — |
| `loan_amount_changed` | `Slider.onChangeEnd`, когда пользователь отпускает слайдер | `amount`: int (`_amount.round()`) |
| `terms_accepted` | чекбокс переключили с `false` на `true` | — |
| `registration_continue_tapped` | нажатие Continue, перед переходом на `/offers` | `amount`: int, `terms`: bool |
| `offers_scrolled` | `offer_screen.dart`, `ScrollEndNotification` у списка | `offset`: double (`metrics.pixels`) |

## Решения

Главная цель: не слать событие на каждый кадр или нажатие клавиши. Мы на бесплатном тарифе PostHog, а лишние события ещё и испортили бы воронку.

- **email/phone started** отправляются один раз за время жизни экрана (флаги `_emailStartedSent` / `_phoneStartedSent`), а не на каждую клавишу. Флаги не сбрасываются, если пользователь очистит поле и начнёт заново.
- **loan_amount_changed** висит на `onChangeEnd`, а не на `onChanged`: `onChanged` срабатывает на каждый кадр перетаскивания. Получается одно событие на одно движение слайдера с итоговой суммой.
- **terms_accepted** отправляется только когда галочку ставят. Когда её снимают, событие не уходит. Если поставить её повторно, событие уйдёт ещё раз.
- **offers_scrolled** отправляется один раз в конце каждого жеста прокрутки, а не на каждый пиксель. `offset` — позиция списка в момент остановки.
- **PII**: email и телефон не передаются ни в одном событии, в свойствах есть только `amount`, `terms` и `offset`.
- Экранные просмотры по-прежнему отслеживает `PosthogObserver`, отдельных событий для них не добавлял.

## Изменённые файлы
- `lib/screens/registration_screen.dart`
- `lib/screens/offer_screen.dart`

## Проверка
- `dart format lib` и `flutter analyze` прошли, ошибок нет.
- Тестов в проекте нет. На устройстве и в эмуляторе не запускал, события в PostHog не отправлялись.
- `flutter analyze` сам переписал `analysis_options.yaml` и создал `.dart_tool/` и `pubspec.lock`. Эти изменения я откатил, в репозитории остались только два экрана и этот файл.
