#!/bin/bash

SUDO_USER=$SUDO_USER
echo "Executing service in '$SUDO_USER'"
current_dir=$(pwd)
echo "Текущая директория: $current_dir"

text="[Unit]
Description=Stat
After=syslog.target network.target

[Service]
WorkingDirectory=$current_dir
ExecStart=$current_dir/venv/bin/python3 stat.py

Restart=always
RestartSec=120

[Install]
WantedBy=multi-user.target"

echo "$text" > stat.service


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

echo 'Cконфигурируем сервис:'
echo 'Создадим ссылку на файл stat.service...'
ln -s /stat.service /etc/systemd/system/stat.service
echo 'OK.'
echo 'Установим права 664 на файл stat.service...'
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