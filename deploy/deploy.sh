#!/bin/bash

# Запускать в папке проекта (/opt/testbot)
#apt-get update
apt install -y python3-pip
apt install -y python3-venv

# создадим виртуальное окружение и установим в него зависимости согласно requirements.txt
python3 -m venv ubuntu_env

source ubuntu_env/bin/activate

pip install -r requirements.txt

deactivate

# дадим право на исполнение скрипта запуска
chmod +x run.sh

# сконфигурируем сервис
ln -s "$HOME"/stat/stat.service /etc/systemd/system/stat.service
chmod 664 /etc/systemd/system/stat.service
systemctl daemon-reload

# добавим в автозагрузку
systemctl enable stat

systemctl status stat