Содержимое:

1. util / parse_maii_to_db.py - скрипт парсер МАИИ.

2. util / data.db - актуальные данные на 30.05.2024 (1373 записи).

Формат БД:
```
date       : name                               : tournament_id : player_id
30.05.2024 : Синхрон Нехрустальной совы. День 2 : 10702         : 82887;27831;7148;...
```

>[!WARNING]
>Under Construction. (нужны абсолютные пути иначе не создаются символьные ссылки...).
>
>Deploy:
> 1. Скопировать файлы из папки deploy в $HOME/stat на виртуалке.
> 2. chmod +x deploy.sh    
> 3. sudo ./deploy.sh
> 3. 
