from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import random
import sqlite3
import time

from bs4 import BeautifulSoup
import requests

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a rotating file handler
handler = RotatingFileHandler('../error.log', maxBytes=100000, backupCount=2)  # 100000 bytes = 100 KB
formatter = logging.Formatter('%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
handler.setFormatter(formatter)

# Add the handler to the root logger
logger.addHandler(handler)

connection = sqlite3.connect('../data.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    name TEXT NOT NULL,
    tournament_id INTEGER NOT NULL,
    player_id TEXT
)
''')


def check_day(date: str) -> bool:
    """
    Check if the given date is earlier than today.

    Parameters:
        date (str): The date to be checked in the format '%d.%m.%Y'.

    Returns:
        bool: True if the given date is earlier than today, False otherwise.
    """
    # Создаем объекты datetime
    date = datetime.strptime(date, '%d.%m.%Y')
    today = datetime.today()

    return date < today


def check_page_update() -> bool:
    """
    Check if the page has been updated by comparing the hash of the page content with the hash stored in 'hash.txt'.
    If the hashes are different, update 'hash.txt' with the new hash and log a message indicating that the page
    is being parsed.

    Returns:
        bool: True if the page has been updated, False otherwise.
    """
    with open('hash.txt', 'w+') as f:
        old_hash = f.read()
        new_hash = str(hash(response.content))
        if old_hash != new_hash:
            f.write(new_hash)
            logging.info('Start parse updated page.')
            return True
    return False


def parse(url: str) -> str:
    """
    Parses the given URL and extracts the player IDs from the HTML content.

    Args:
        url (str): The URL to parse.

    Returns:
        str: A semicolon-separated string of players IDs extracted from the HTML content.
    """
    base_url = 'https://rating.maii.li/'
    full_url = base_url + url
    response = requests.get(full_url)

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    player_id = []
    for i in soup.find_all('a', {'class': 'hover:underline text-sm'}):
        player_id.append(i['href'].split('/')[-2])

    return ';'.join(player_id)


url = 'https://rating.maii.li/b/tournaments/'
response = requests.get(url)

soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

tournament_data = []
for index, row in enumerate(soup.select('tbody tr')):
    date = row.select_one('td:nth-child(1)').text.strip()

    if not check_day(date):
        logging.info(f'Skip {index} - {date}')
        continue

    tournament_cell = row.select_one('td:nth-child(2) a')
    tournament_name = tournament_cell.text.strip()
    tournament_id = tournament_cell['href'].split('/')[-2]
    player_id = parse(url=tournament_cell['href'])

    if player_id:
        tournament_data.append((date, tournament_name, tournament_id, player_id))
        print(index, '-', tournament_name)
        time.sleep(random.randint(5, 7))

cursor.executemany('''
INSERT INTO tournaments (date, name, tournament_id, player_id)
VALUES (?, ?, ?, ?)
''', tournament_data)
connection.commit()
connection.close()
