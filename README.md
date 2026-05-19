# GuardSaaS Plates для Home Assistant

Минимальная custom integration для получения разрешённых автомобильных номеров из GuardSaaS.

## Установка

1. Распакуйте архив.
2. Скопируйте папку:

```text
custom_components/guardsaas_plates
```

в папку конфигурации Home Assistant:

```text
/config/custom_components/guardsaas_plates
```

3. Перезапустите Home Assistant.
4. Откройте:

```text
Настройки → Устройства и службы → Добавить интеграцию
```

5. Найдите `GuardSaaS Plates`.
6. Введите логин и пароль GuardSaaS.

## Что создаётся

Интеграция создаёт одно устройство `GuardSaaS Plates` и сущности:

- `sensor.*_allowed_plates` — основной сенсор со списком номеров в атрибутах;
- `sensor.*_plates_count` — количество номеров;
- `sensor.*_last_update` — время последнего обновления;
- `binary_sensor.*_authentication` — статус последней авторизации;
- `button.*_refresh_plates` — ручное обновление.

## Важные атрибуты

В основном сенсоре есть атрибуты:

- `count`
- `content`
- `plates_data`
- `timestamp`
- `status`
- `from_cache`
- `error`

## Кеш

По умолчанию кеш создаётся в:

```text
/config/.guardsaas_allowed_license_plate_numbers.json
```

Если GuardSaaS временно недоступен или авторизация не прошла, интеграция попробует использовать кеш.

## Интервал обновления

По умолчанию: 3 часа.
