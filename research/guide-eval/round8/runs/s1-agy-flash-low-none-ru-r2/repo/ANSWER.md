# Изменения в генераторе тренировок

## Что изменено
В файле [`gen.py`](file:///tmp/h-Dk0GLw/gen.py) в функции [`hr_target`](file:///tmp/h-Dk0GLw/gen.py#L10-L13) ключ `"value"` заменён на `"start"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Причина изменений
В Intervals.icu схема целевых показателей шага тренировки (`workout_doc.steps[].hr`):
- Использование пары `{"value": lo, "end": hi}` воспринимается сервисом как Lap-HR / маппинг на стандартные зоны пульса (zone-mapped target). При экспорте в Garmin FIT файл такой шаг транслируется как привязка к пульсовой зоне устройства, из-за чего часы Garmin подменяют границы диапазона собственными локальными границами зон (Z1–Z5), игнорируя точные проценты LTHR.
- Использование пары явных границ `{"start": lo, "end": hi}` указывает Intervals.icu на произвольный коридор значений (Instant-HR corridor). В этом случае Intervals.icu рассчитывает точные абсолютные значения bpm от заданного LTHR атлета и передаёт в Garmin FIT именно точный диапазон, не обрезая его под пульсовые зоны часов.
