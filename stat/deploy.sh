#!/bin/bash

SUDO_USER=$SUDO_USER
echo "Executing service in '$SUDO_USER'"

# Запускать в папке проекта
#apt-get update
apt install -y python3-pip
apt install -y python3-venv

echo "Создадим виртуальное окружение и установим в него зависимости согласно requirements.txt"
python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

deactivate
echo "Виртуальное окружение создано."
echo "****************************"

# дадим право на исполнение скрипта запуска
#chmod +x run.sh

echo 'Cконфигурируем сервис:'
echo 'Создадим ссылку на файл stat.service...'
ln -s /home/"$SUDO_USER"/stat/stat.service /etc/systemd/system/stat.service
echo 'OK.'
echo 'Сделаем права на файл stat.service...'
chmod 664 /etc/systemd/system/stat.service
echo 'OK.'
echo 'Обновим конфигурацию systemd...'
systemctl daemon-reload
echo 'OK.'
echo '****************************'


echo 'Добавим в автозагрузку...'
systemctl enable stat
echo 'OK.'
echo 'Запустим сервис...'
systemctl start stat
echo 'OK.'
echo 'Проверим статус...'
systemctl status stat