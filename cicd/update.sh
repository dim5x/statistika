#!/bin/bash

if [ -f "statistika/data.db" ]; then
    mv statistika/data.db .
    echo "File data.db moved successfully."
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


