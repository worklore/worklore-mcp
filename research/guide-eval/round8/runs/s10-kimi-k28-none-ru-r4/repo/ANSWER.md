# Реализация событий аналитики

Реализованы все 6 событий из `docs/EVENTS.md` через существующую обёртку `Analytics` (`lib/analytics.dart`). Имена и типы свойств совпадают со спецификацией, PII (email, телефон) не отправляется.

## Экран регистрации (`lib/screens/registration_screen.dart`)

| Событие | Триггер | Свойства |
|---|---|---|
| `registration_email_started` | Первое нажатие клавиши в поле Email (один раз за визит экрана, флаг `_emailStarted`) | — |
| `registration_phone_started` | Первое нажатие клавиши в поле Phone (один раз, флаг `_phoneStarted`) | — |
| `loan_amount_changed` | Каждое движение слайдера суммы займа | `amount` (int, округлённое значение) |
| `terms_accepted` | Только при установке галочки (не при снятии) | — |
| `registration_continue_tapped` | Тап по кнопке Continue до навигации на `/offers` | `amount` (int), `terms` (bool) |

## Экран предложений (`lib/screens/offer_screen.dart`)

- `OfferScreen` переведён с `StatelessWidget` на `StatefulWidget` ради `ScrollController`.
- `offers_scrolled` — слушатель контроллера отправляет событие на каждое изменение позиции скролла со свойством `offset` (double, текущее смещение `_scroll.offset`). Контроллер освобождается в `dispose()`.

## Решения и примечания

- «Started»-события (`registration_email_started`, `registration_phone_started`) отправляются по одному разу на открытие экрана — соответствует шагам воронки.
- `terms_accepted` отправляется только при переходе галочки в «принято», а не при каждом переключении.
- `loan_amount_changed` и `offers_scrolled` отправляются на каждое изменение (движение слайдера / скролла). Для скролла это может быть много событий при долгой прокрутке — если понадобится, можно добавить троттлинг, но в спецификации он не требовался.
- Просмотры экранов не трекаются — они уже автоматические через `PosthogObserver` (см. `docs/EVENTS.md`).
- Ничего не отправлялось и не публиковалось во внешние сервисы: изменения только в локальных файлах.

## Проверка

Полный `flutter analyze` / `dart analyze` запустить не удалось — в этой среде исполнение бинарников Flutter/Dart запрещено (Operation not permitted). Код проверен вручную: типы свойств совместимы с сигнатурой `Analytics.capture(String, [Map<String, Object>?])`, события вызываются из не-async колбэков (предупреждений о не-awaited Future не будет). Рекомендую прогнать `flutter analyze` локально.
