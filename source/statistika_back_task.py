import queue
import sqlite3
import time

import requests

import statistika_logger

log = statistika_logger.get_logger(__name__)


def update_player_tournaments(player_ids_queue: queue.Queue) -> None:
    """
    Updates the tournaments in the database by fetching the tournaments from the internet and comparing them
    with the tournaments in the database.

    Parameters:
        player_ids_queue (queue.Queue): A queue containing player IDs.

    Returns:
        None
    """
    log.warning('Update DB started.')

    with sqlite3.connect('../data.db') as db_connection:
        cursor = db_connection.cursor()

        while True:
            if player_ids_queue:  # Работаем, если в очереди есть данные.
                player_ids = player_ids_queue.get()

                for player_id in player_ids:  # Проход по всем игрокам.
                    try:
                        # Запрос на получение турниров игрока из БД и Веб.
                        tournaments_in_db = get_tournaments_from_db(cursor, player_id)
                        tournaments_in_web = get_tournaments_from_web(player_id)

                        # Коли записи разнятся, обновляем БД.
                        if tournaments_in_web != tournaments_in_db:
                            log.warning(f'Обновляем запись турниров в БД для игрока: {player_id}.')
                            update_db(cursor, player_id, tournaments_in_web)
                            time.sleep(2)

                    # Если 404, то предполагаем неполадки сети, логируем, ждём 1 час и продолжаем.
                    except Exception as e:
                        log.error(e)
                        time.sleep(60 * 60)
                        continue
            time.sleep(10)  # Спим 10 сек, если в очереди нет данных.


def get_tournaments_from_db(cursor, player_id):
    query = 'SELECT tournaments FROM players WHERE player_id = ?'
    return cursor.execute(query, (player_id,)).fetchall()[0][0]


def get_tournaments_from_web(player_id):
    url = f'https://api.rating.chgk.net/players/{player_id}/tournaments'
    response = requests.get(url=url)
    if response.status_code != 200:
        raise Exception(f'Something wrong with request to API. Status code: {response.status_code}, from {url}')
    return ','.join(str(i['idtournament']) for i in response.json())


def update_db(cursor, player_id, tournaments):
    query = 'UPDATE players SET tournaments = ? WHERE player_id = ?'
    cursor.execute(query, (tournaments, player_id))
    cursor.connection.commit()


def watchdog(player_ids_queue: queue.Queue) -> None:
    """
    Runs a watchdog process that periodically retrieves the player IDs from the 'players' table in the 'data.db'
    database and puts them into the provided queue.
    The function runs in an infinite loop and sleeps for 24 hours between each iteration.

    Parameters:
    player_ids_queue (queue.Queue): The queue to put the player IDs into.

    Returns:
    - None
    """
    while True:
        log.warning('Watchdog started.')
        connection = sqlite3.connect('../data.db')
        cursor = connection.cursor()

        # Получаем список ID игроков
        query = "SELECT player_id FROM players"
        players_ids: list[str] = [row[0] for row in cursor.execute(query).fetchall()]

        # Кладём список в очередь.
        player_ids_queue.put(players_ids)

        # Закрываем соединение с БД
        cursor.close()
        connection.close()

        # Спим 24 часа
        time.sleep(60 * 60 * 24)
