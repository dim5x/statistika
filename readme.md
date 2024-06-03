Содержимое:

1. stat.py - основной скрипт.

2. util / parse_maii_to_db.py - скрипт парсер МАИИ.

3. util / data.db - актуальные данные на 30.05.2024 (1373 записи).
4. js / table_main.js - обработчик главной таблицы.
5. js / table_players.js - обработчик таблицы игроков.

Формат БД:

Таблица tournaments:
```
id : date       : name                               : tournament_id : player_id
1  : 30.05.2024 : Синхрон Нехрустальной совы. День 2 : 10702         : 82887;27831;7148;...
```
Таблица players:
```
id : fio         : player_id                      
1  : Иван Иванов : 10702
```
Таблица team_scores:
```
id : team_name  : Сумма  : 07-03-24 : 14-03-24                      
1  : Паравозики : 107.02 : 12       : 14.5
```


Команда развёртывания / установки:

    git clone https://github.com/dim5x/statistika.git && cd statistika && chmod +x deploy.sh && sudo ./deploy.sh
