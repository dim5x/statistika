from datetime import datetime, timedelta
import hashlib
import os
import queue
import sqlite3
import time
from threading import Thread

from flask import Flask, g, jsonify, redirect, render_template, request, session
from flask_cors import CORS
import requests

from cicd import db_initialization
import db_management
import statistika_logger

app = Flask(__name__)
app.secret_key = os.urandom(24)  # для работы session

CORS(app)

log = statistika_logger.get_logger(__name__)

q = queue.Queue()


def get_db_connection() -> sqlite3.Connection:
    """
    Функция, которая получает соединение с базой данных.
    Если соединение не существует, устанавливает новое соединение с использованием SQLite с 'data.db'.
    Возвращает существующее или новосозданное соединение с базой данных.
    """
    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        # для тестирования
        # раскомментировать, если необходимо пересоздать БД
        # os.remove('../data.db')
        if not os.path.exists('../data.db'):
            db_connection = g._database = sqlite3.connect('../data.db')
            db_initialization.create_tables(db_connection)
            db_initialization.load_test_data(db_connection)
        else:
            db_connection = g._database = sqlite3.connect('../data.db')
    return db_connection


@app.teardown_appcontext
def close_db_connection(exception: Exception) -> None:
    """
    Функция завершения, которая закрывает соединение с базой данных.
    Параметры:
    - exception: Исключение, которое вызвало завершение, если таковое имеется.
    """
    db_connection = getattr(g, '_database', None)
    if db_connection is not None:
        db_connection.close()


def update_players_tournaments(q: queue.Queue) -> None:
    """
    Update the tournaments in the DB by fetching the tournaments from the internet and comparing them
    with the tournaments in the DB.

    Parameters:
        q (queue.Queue): A queue containing player IDs.

    Returns:
        None
    """
    log.warning('Start updating players tournaments...')

    # Подключаемся к БД.
    with sqlite3.connect('../data.db') as con:
        cursor = con.cursor()

    while True:
        # Если в очереди есть данные, то берём их в обработку.
        if q:
            players_ids = q.get()

            # Проход по всем игрокам.
            for player_id in players_ids:
                # Запрос на получение турниров игрока из БД.
                query = 'SELECT tournaments FROM players WHERE player_id = ?'
                tournaments_in_db: str = cursor.execute(query, (player_id,)).fetchall()[0][0]

                # Запрос на получение турниров игрока {player_id} из Интернета.
                log.warning(f'Запрос на получение турниров игрока {player_id} из Интернета.')
                try:
                    url = f'https://api.rating.chgk.net/players/{player_id}/tournaments'
                    with requests.get(url=url) as response:
                        if response.status_code != 200:
                            raise Exception(
                                f'Something wrong with request to API. Status code: {response.status_code}, from {url}')

                    tournaments_in_web = [i['idtournament'] for i in response.json()]
                    tournaments_in_web = ','.join(map(str, tournaments_in_web))

                    # Коли записи разнятся, обновляем БД.
                    if tournaments_in_web != tournaments_in_db:
                        log.warning(f'Обновляем запись турниров в БД для игрока: {player_id}.')
                        query = 'UPDATE players SET tournaments = ? WHERE player_id = ?'
                        cursor.execute(query, (tournaments_in_web, player_id))
                        con.commit()
                        time.sleep(2)

                # Если 404, то предполагаем неполадки сети, логируем, ждём 1 час и продолжаем.
                except Exception as e:
                    log.error(e)
                    time.sleep(60 * 60)  # 1-hour sleep after error
                    # time.sleep(5)
                    continue
        time.sleep(10)


def watchdog(q: queue.Queue) -> None:
    """
    Runs a watchdog process that periodically retrieves the player IDs from the 'players' table in the 'data.db'
    database and puts them into the provided queue.
    The function runs in an infinite loop and sleeps for 24 hours between each iteration.

    Parameters:
    - q (queue.Queue): The queue to put the player IDs into.

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
        q.put(players_ids)

        # Закрываем соединение с БД
        cursor.close()
        connection.close()

        # Спим 24 часа
        time.sleep(60 * 60 * 24)


workers = [Thread(target=update_players_tournaments, args=(q,), name='check_once'),
           Thread(target=watchdog, args=(q,), name='watchdog')]

for w in workers:
    w.start()


@app.route('/')
def index():
    """
    Обработчик маршрута для корневого URL-адреса ("/").

    Очищает сеанс, извлекает данные из БД,
    добавляет имена столбцов в начало данных, преобразует данные в формат JSON, сортирует их по полю "_sum_minus_2",
    а затем отображает шаблон index.html с отсортированными данными и именами столбцов.
    """
    session.clear()

    # Получаем данные из базы
    db_connection = get_db_connection()
    data, columns = db_management.get_maintable(db_connection)

    # Добавление названий столбцов в начало
    thead = ['Команда', 'Сумма', 'Сумма - 2'] + columns[3:]

    # Преобразование данных в формат JSON
    json_data = to_json(data, columns)

    # Сортировка по сумме
    data = sorted(json_data, key=lambda x: x['_sum_minus_2'], reverse=True)

    return render_template('index.html', thead=thead, data=data)


@app.route('/login', methods=['POST', 'GET'])
def admin_login():
    """
    Обрабатывает логин в систему. Считывает с формы логин/пароль (index.html).

    Проверяет в базе наличие хэша пароля. В случае успеха делает редирект на основную страницу.
    Помечает успешный залогин в кукисе session[login] = login.
    В противном случае - пишет Fail и отображает страницу ввода пароля снова.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    log.info('Logon.')

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        query = 'SELECT salt FROM users WHERE login = :login'
        login_exists = cursor.execute(query, {'login': login}).fetchall()

        if login_exists:
            log.info('There is a salt')
            salt = login_exists[0][0]

            password_hash = hashlib.scrypt(password=bytes(password, encoding='UTF-8'),
                                           salt=bytes(salt, encoding='UTF-8'),
                                           n=2 ** 14, r=8, p=1, dklen=64).hex()

            query = """
                    SELECT
                        count(1) _count
                    FROM
                        users
                    WHERE 
                        login =:login
                        AND 
                        hash =:hash
                """

            data = {'login': login, 'hash': password_hash}

            if cursor.execute(query, data).fetchall()[0][0]:
                session['login'] = login
                return redirect('/main_table')
        else:
            return render_template('login.html', message='Fail.')

    return render_template('login.html')


@app.route('/main_table')
def main_table():
    """
    Функция, которая служит обработчиком маршрута для таблицы. Отображает шаблон 'main_table.html'.
    """
    log.info('Function main_table() was called...')

    thread_status = '&#128994;' if w.is_alive() else '&#128308;'

    if session.get('login'):
        if request.method == 'GET':
            return render_template('main_table.html', thread_status=thread_status)
        if request.method == 'POST':
            log.debug(request.data)
    else:
        return redirect('/login')


@app.route('/add_game', methods=['GET'])
def add_game() -> str:
    """
    Отображает шаблон add_game.html и возвращает визуализированный HTML в виде строки.

    Эта функция является обработчиком маршрута для конечной точки URL-адреса «/add_game». Он принимает запросы GET
    и возвращает обработанный шаблон add_game.html в виде строки.
    """
    return render_template('add_game.html')


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    """
    Отображает шаблон add_player.html и возвращает визуализированный HTML в виде строки.

    Эта функция является обработчиком маршрута для конечной точки URL-адреса «/add_player». Он принимает запросы GET
    и возвращает обработанный шаблон add_game.html в виде строки.
    """
    db_connection = get_db_connection()
    # Получаем список команд
    teams = [i[0] for i in db_management.get_teams(db_connection)]
    return render_template('add_player.html', teams=teams)


@app.route('/add_score', methods=['GET', 'POST'])
def add_score():
    db_connection = get_db_connection()
    data = [i[0] for i in db_management.get_teams(db_connection)]

    message = ''
    if request.method == 'POST':
        log.debug(request.form)
        message = 'Данные внесли.'
    return render_template('add_score.html', data=data, message=message)


@app.route('/add_team', methods=['GET'])
def add_team():
    return render_template('add_team.html')


@app.route('/get_columns', methods=['GET'])
def get_columns() -> list[dict]:
    """
    Функция для извлечения названий столбцов из таблицы базы данных и преобразования их в определенный формат
    для отображения.
    """
    # Подключение к базе данных SQLite и получение данных для главной таблицы
    db_connection = get_db_connection()
    _, columns = db_management.get_maintable(db_connection)

    transformed_columns = []

    # Цикл для преобразования каждого элемента массива строк в объект
    for column in columns:
        if column == 'team_name':
            field_title = "Команда"
        elif column == '_sum_':
            field_title = 'Cумма'
        elif column == '_sum_minus_2':
            field_title = 'Cум(-2)'
        else:
            field_title = '.'.join((column.split('-')[2], column.split('-')[1]))

        transformed_columns.append({
            # Пример условной логики для определения значения editor
            'editor': 'input',  # if column == 'team_name' else 'number'
            'field': column,
            'hozAlign': 'center' if column == 'summa_2' else 'left',
            'sorter': 'number',
            'title': field_title,
            'validator': 'numeric',
            # 'contextMenu': 'cellContextMenu'
        })
    return transformed_columns


def to_json(data, columns):
    """Вспомогательная функция для преобразования данных в формат JSON."""
    log.debug('Function to_json() was called...')
    json_data = []
    for row in data:
        row_data = {}
        for i, column in enumerate(columns):
            row_data[column] = row[i]
        json_data.append(row_data)

    return json_data


@app.route('/get_data', methods=['GET'])
def get_data():
    """
    Обработчик основной конечной точки для получения данных /get_data.
    """
    if request.referrer is None:
        return 'Що таке?'

    db_connection = get_db_connection()

    who = request.referrer.split('/')[-1]
    match who:
        case 'main_table':
            data, columns = db_management.get_maintable(db_connection)
            return to_json(data, columns)
        case 'add_player':
            data = db_management.get_players(db_connection)
            log.debug(data)
            columns = ['fio', 'player_id', 'team_name']  # менять на человеческие 'ФИО', 'ИД игрока' в table_players.js
            return to_json(data, columns)
        case 'add_team':
            data = db_management.get_teams(db_connection)
            columns = ['Name']
            return to_json(data, columns)


@app.route('/check_packet', methods=['POST'])
def check_packet():
    """Проверка играли ли игроки в этом пакете."""
    log.debug(request.json)
    db_connection = get_db_connection()

    answer = []
    # p={}

    players = db_management.get_players(db_connection)
    p = {i[0]: i[1] for i in players}  # {'Леонов Александр': '59778', 'Чечекин Максим': '172423'},

    tournaments = db_management.get_tournaments(db_connection)

    d = {}
    packets = [i for i in request.json if i]
    for packet in packets:
        d[packet] = [i[0] for i in tournaments if (i[1] and packet in i[1].split(','))]
        # print(d[packet]) # ['Леонов Александр', 'Чечекин Максим', 'Вишнякова Наталья']
        if d[packet]:
            b = [f'<a href="https://rating.maii.li/b/player/{p[i]}"/>{i}</a>' for i in d[packet]]
            print(b)
            answer.append(
                f'В турнире <a href="https://rating.maii.li/b/tournament/{packet}/">{packet}</a> играл(и): {b} <br>')
        else:
            answer.append(f'В турнире <a href="https://rating.maii.li/b/tournament/{packet}/">{packet}</a> никто не играл. <br>')
    return jsonify(success=True, data=''.join(answer))


@app.route('/test', methods=['POST', 'GET'])
def test():
    if request.method == 'POST':
        log.debug(request.data.decode('utf-8'))
        data = request.data.decode('utf-8')
        log.info('OK')
    # json_data = [
    #     {'id': 1, 'name': "Tiger Nixon", 'position': "System Architect", 'office': "Edinburgh", 'extension': "5421",
    #      'startDate': "2011/04/25", 'salary': "Tiger Nixon"}
    # ]
    # lll = {'data': [[1, 'test', 78],
    #               [2, 'test2', 145],
    #               [3, 'test3', 23],
    #               [4, 'test4', 45]],
    #      'columns': ['id', 'name', 'position']
    #      }

    return render_template('tablecelledit.html')


@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        db_connection = get_db_connection()
        who = request.referrer.split('/')[-1]
        match who:
            case 'main_table':
                log.debug(request.json)
                date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                db_management.update_main_table(db_connection, request.json, date)
                # case 'add_player':
            #     return render_template('add_player.html')
            # case 'add_team':
            #     return render_template('add_team.html')
    return {'success': True}


# @app.route('/update_from_github', methods=['POST', 'GET'])
# def update_from_github() -> jsonify:# todo
#     """
#     Функция для обновления данных из GitHub.
#     Эта функция скачивает последние изменения в репозитории и обновляет проект.
#     """
#     # print(request.json)
#     cmd = 'echo "kek" > lol.kek'
#     os.system(cmd)
#     # cmd = 'sudo touch lol.kek'
#     cmd = 'sudo ./update.sh'
#     os.system(cmd)
#     print(cmd)
#     # return jsonify(success=True, data=request.json)
#     return str(request.json)


@app.route('/update_table_players', methods=['POST'])
def update_table_players():
    """
    Функция для обновления таблицы игроков данными, полученными через POST-запрос.
    Эта функция добавляет нового игрока в таблицу players, используя его полное имя (fio) и идентификатор игрока.
    В случае успешного выполнения возвращает JSON-ответ с сообщением об успехе, в противном случае возвращает сообщение
    об ошибке.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    try:
        d = request.json
        log.debug(d)
        fio = d['playerFIO']
        player_id = d['playerName']
        team_name = d['teamName']
        log.debug((fio, player_id, team_name))
        # Получаем идентификатор команды
        query = 'select id from teams where name = ?'
        cursor.execute(query, (team_name,))
        team_id = cursor.fetchone()[0]
        log.debug(team_id)
        # Записываем данные в таблицу players
        query = 'insert into players (fio, player_id, team_id) values (?, ?, ?)'
        cursor.execute(query, (fio, player_id, team_id))
        db_connection.commit()
        q.put([player_id])
        log.info(f'Записали игрока {fio} в таблицу players.')

        response = {'success': True}
        return jsonify(response)

    except Exception as e:
        log.error(f'Error: {e}')
        return jsonify(success=False, error=str(e))


@app.route('/update_table_teams', methods=['POST'])
def update_table_teams():
    """
    Функция для обновления таблицы команд данными, полученными через POST-запрос.
    Эта функция добавляет новую команду в таблицу teams.
    В случае успешного выполнения возвращает JSON-ответ с сообщением об успехе, в противном случае возвращает сообщение
    об ошибке.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    try:
        log.debug(request.json)
        d = request.json
        log.debug(type(d))
        t_name = d['team_name']
        query = 'INSERT INTO teams(name) VALUES (?)'
        cursor.execute(query, (t_name,))
        db_connection.commit()

        response = {'success': True}
        return jsonify(response)

    except Exception as e:
        log.error(f'Error: {e}')
        return jsonify(success=False, error=str(e))


@app.errorhandler(404)
def page_not_found(error):
    """Отображает страницу ошибки в случае перехода на несуществующую страницу."""
    return render_template('404.html', error=error), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)
