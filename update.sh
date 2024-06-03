#!/bin/bash

if [ -f "data.db" ]; then
    mv data.db ../
    echo "File data.db copied successfully."
    systemctl disable stat
    rm -rf /home/dim5x/statistika
    git clone https://github.com/dim5x/statistika.git && cd statistika && chmod +x deploy.sh && sudo ./deploy.sh
    mv ../data.db .
else
    echo "File data.db does not exist."
    systemctl disable stat
    rm -rf /home/dim5x/statistika
    git clone https://github.com/dim5x/statistika.git && cd statistika && chmod +x deploy.sh && sudo ./deploy.sh

fi


