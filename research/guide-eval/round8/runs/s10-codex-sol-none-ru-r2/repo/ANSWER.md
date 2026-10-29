# Реализованные события аналитики

- На экране регистрации через `Analytics.capture` добавлены `registration_email_started` и `registration_phone_started` при первом вводе в соответствующие поля. Адрес и номер в свойства не передаются.
- `loan_amount_changed` отправляется после изменения ползунка с целочисленным `amount`; `terms_accepted` — при установке флажка; `registration_continue_tapped` — при нажатии активной кнопки с `amount` и `terms`.
- На экране предложений `offers_scrolled` отправляется по завершении прокрутки со смещением `offset` типа `double`.

События просмотра экранов по-прежнему обрабатывает существующий `PosthogObserver`.

Проверка: `dart format` выполнен, `git diff --check` прошёл. `flutter analyze --no-pub` не смог проверить код: в этой копии проекта отсутствуют разрешённые зависимости Flutter, PostHog и `flutter_lints`. Зависимости не загружались, внешние сервисы не вызывались.
