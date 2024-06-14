import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session
from flask_cors import CORS
import requests

from cicd import db_initialization
import db_management

# from typing import List

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # для работы session

CORS(app)


def get_db_connection() -> sqlite3.Connection:
    """
    Функция, которая получает соединение с базой данных.
    Если соединение не существует, устанавливает новое соединение с использованием SQLite с 'data.db'.
    Возвращает существующее или новосозданное соединение с базой данных.
    """

    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        # для тестирования
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


@app.route('/')
def index():
    session.clear()

    db_connection = get_db_connection()
    data = db_management.get_maintable(db_connection)

    # Получение названий столбцов из результирующего набора
    columns = [description[0] for description in data.description]

    # Добавление названий столбцов в начало
    thead = ['Команда', 'Сумма', 'Сумма - 2'] + columns[3:]

    # Преобразование данных в формат JSON
    json_data = []
    for row in data:
        row_data = {}
        for i in range(0, len(columns)):
            row_data[columns[i]] = row[i]
        json_data.append(row_data)

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

    print('logon')

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        password_hash = hashlib.sha3_384(bytes(password, encoding='UTF-8')).hexdigest()

        query = '''
                    select
                        count(1) _count
                    from
                        login
                    where
                        user =:login
                        and
                        hash =:hash
                '''
        data = {'login': login, 'hash': password_hash}

        if cursor.execute(query, data).fetchall()[0][0]:
            session[login] = login
            return redirect('/maintable')
        else:
            return render_template('login.html', message='Fail.')

    return render_template('login.html')


@app.route('/main_table')
def main_table() -> str:
    """
    Функция, которая служит обработчиком маршрута для таблицы. Отображает шаблон 'main_table.html'.
    """
    print('Function main_table() was called...')
    if request.method == 'POST':
        print(request.data)
    return render_template('main_table.html')


@app.route('/add_game', methods=['GET'])
def add_game() -> str:
    return render_template('add_game.html')


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    return render_template('add_player.html')


@app.route('/add_score', methods=['GET', 'POST'])
def add_score():
    db_connection = get_db_connection()
    data = [i[0] for i in db_management.get_teams(db_connection)]

    message = ''
    if request.method == 'POST':
        print(request.form)
        message = 'Данные внесли.'
    return render_template('add_score.html', data=data, message=message)


@app.route('/add_team', methods=['GET'])
def add_team():
    return render_template('add_team.html')


@app.route('/get_columns', methods=['GET'])
def get_columns() -> list[dict]:
    """
    Функция для извлечения названий столбцов из таблицы базы данных и преобразования их в определенный формат для отображения.
    """
    # Подключение к базе данных SQLite
    db_connection = get_db_connection()
    data = db_management.get_maintable(db_connection)

    columns = [description[0] for description in data.description]

    transformed_columns = []

    # Цикл для преобразования каждого элемента массива строк в объект
    for column in columns[:]:
        if column == "team_name":
            field_title = "Команда"
        elif column == "_sum_":
            field_title = "Cумма"
        elif column == "_sum_minus_2":
            field_title = "Cумма (-2)"
        else:
            field_title = column

        transformed_columns.append({
            "title": field_title,
            "field": column,
            "editor": "input",  # if column == "team_name" else "number"
            # Пример условной логики для определения значения editor
            'sorter': 'number',
            'hozAlign': 'center' if column == 'summa_2' else 'left',
            # 'contextMenu': 'cellContextMenu'
            'validator': 'numeric',

        })

    # Вывод преобразованных объектов
    # print(f'{transformed_columns=}')
    # print(transformed_columns)
    return jsonify(transformed_columns)


def to_json(data, columns):
    print('Function to_json() was called...')
    json_data = []
    for row in data:
        row_data = {}
        for i in range(0, len(columns)):
            row_data[columns[i]] = row[i]
        json_data.append(row_data)
    # print(f'{json_data=}')
    return json_data


@app.route('/get_data', methods=['GET'])
def get_data():
    if request.referrer is None:
        return 'Що таке?'

    db_connection = get_db_connection()

    who = request.referrer.split('/')[-1]
    match who:
        case 'main_table':
            data = db_management.get_maintable(db_connection)
            columns = [description[0] for description in data.description]
            return to_json(data, columns)
        case 'add_player':
            data = db_management.get_players(db_connection)
            columns = ['id', 'fio', 'player_id']
            return to_json(data, columns)
        case 'add_team':
            data = db_management.get_teams(db_connection)
            columns = ['Name']
            return to_json(data, columns)


@app.route('/check_packet', methods=['POST'])
def check_packet() -> jsonify:
    print(request.json)
    packets = [i for i in request.json if i]
    answer = []
    for packet_id in packets:
        r = requests.get(f'https://rating.maii.li/b/tournament/{packet_id}/')
        # print(r.text)
        pattern = r'/\/b\/player\/(\d+)/gm'
        matches = re.findall(pattern, r.text)
        print(matches)
        print(len(matches))
        answer.append(matches)

    return jsonify(success=True, data=''.join(answer))


# @app.route('/set_result', methods=['POST'])
# def set_result():
#     db_connection = get_db_connection()
#     cursor = db_connection.cursor()
#     # print('result')
#     # print(request.json)
#
#     # Получение названий всех колонок
#     cursor.execute("PRAGMA table_info(teams_scores)")
#     columns = [info[1] for info in cursor.fetchall()]
#
#     # Определение колонок для суммирования (те, что имеют формат даты)
#     date_columns = [col for col in columns if "-" in col]
#
#     # Создание части запроса для суммирования значений этих колонок
#     sum_expression = " + ".join([f'COALESCE("{col}", 0)' for col in date_columns])
#
#     # Создание части запроса для суммирования значений этих колонок без двух наименьших значений
#     sum_minus_two_least_expression = f"""
#         SELECT ({sum_expression}) -
#         COALESCE((SELECT SUM(val) FROM (
#             SELECT val FROM (
#                 SELECT {', '.join([f'COALESCE("{col}", 0)' for col in date_columns])} AS val
#                 FROM main."teams_scores-mark_for_deletion" t2
#                 WHERE t2.id = teams_scores.id AND t2.team_name NOT LIKE '%_q%'
#             )
#             ORDER BY val LIMIT 2
#         )), 0)
#         FROM main."teams_scores-mark_for_deletion" t3
#         WHERE t3.id = teams_scores.id AND t3.team_name NOT LIKE '%_q%'
#     """
#     # print(f'{sum_minus_two_least_expression=}')
#     # Генерация полного SQL-запроса для обновления
#     sql_update_query = f"""
#     UPDATE main."teams_scores-mark_for_deletion"
#     SET summa = (
#         SELECT {sum_expression}
#         FROM main."teams_scores-mark_for_deletion" t2
#         WHERE t2.id = "teams_scores-mark_for_deletion".id AND t2.team_name NOT LIKE '%_q%'
#     ),
#     summa_2 = (
#         {sum_minus_two_least_expression}
#     )
#     WHERE team_name NOT LIKE '%_q%';
#     """
#
#     # Выполнение SQL-запроса
#     cursor.execute(sql_update_query)
#     db_connection.commit()
#
#     # Закрытие соединения
#     # conn.close()
#
#     # query = "SELECT player_id, fio FROM main.players"
#     # players_data = cursor.execute(query).fetchall()
#     # # players_set = set([player[0] for player in players_data])
#     # players_dict = {k: v for k, v in players_data}
#     # # print(f'{players_dict=}')
#     #
#     # answer = []
#     # for i in request.json:
#     #     # print(f'{i=}')
#     #     if i:
#     #         query = 'SELECT player_id from tournaments WHERE tournaments.tournament_id = ?'
#     #         tournaments_player_id = cursor.execute(query, (int(i),)).fetchall()
#     #         print(f'{tournaments_player_id=}')
#     #         if not tournaments_player_id:
#     #             answer.append(f'Турнир {i} в базе не найден.')
#     #             continue
#     #         tournaments_player_id_set = set(tournaments_player_id[0][0].split(';'))
#     #         print(f'{tournaments_player_id_set=}')
#     #         intersection = tournaments_player_id_set.intersection(players_dict.keys())
#     #
#     #         # https: // rating.maii.li / b / player / 172423 /
#     #         if intersection:
#     #             answer.append(f'В турнире {i} играл(и): {[players_dict[i] for i in intersection]}')
#     #         else:
#     #             answer.append(f'В турнире {i} никто не играл.')
#     # print(f'{answer=}')
#     # print('\n'.join(answer))
#     # return jsonify(success=True, data='\n'.join(answer))
#     return jsonify(success=True, data=request.json)

@app.route('/test', methods=['POST', 'GET'])
def test() -> list:
    if request.method == 'POST':
        print(request.form)
        print('OK')
    json_data = [
        {'id': 1, 'name': "Tiger Nixon", 'position': "System Architect", 'office': "Edinburgh", 'extension': "5421",
         'startDate': "2011/04/25", 'salary': "Tiger Nixon"}
    ]
    l = {'data': [[1, 'test', 78],
                  [2, 'test2', 145],
                  [3, 'test3', 23],
                  [4, 'test4', 45]],
         'columns': ['id', 'name', 'position']
         }
    m = {
        "data": [
            {
                "id": 1,
                "name": "John Doe",
                "position": "Developer"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "position": "Designer"
            },

        ],

    }

    tabledata = [
        {'id': '1', 'name': "Oli Bob", 'age': "12", 'col': "red", 'dob': ""},
        {'id': '2', 'name': "Mary May", 'age': "1", 'col': "blue", 'dob': "14/05/1982"},
        {'id': '3', 'name': "Christine Lobowski", 'age': "42", 'col': "green", 'dob': "22/05/1982"},
        {'id': '4', 'name': "Brendon Philips", 'age': "125", 'col': "orange", 'dob': "01/08/1980"},
        {'id': '5', 'name': "Margret Marmajuke", 'age': "16", 'col': "yellow", 'dob': "31/01/1999"},
    ]
    # tabledata = [
    #     [1, "Oli Bob", "12", "red", ""],
    #     [1, "Oli Bob", "12", "red", ""],
    #     [1, "Oli Bob", "12", "red", ""],
    #
    # ]

    return tabledata


@app.route('/update_from_github', methods=['POST', 'GET'])
def update_from_github() -> jsonify:
    """
    Функция для обновления данных из GitHub.
    Эта функция скачивает последние изменения в репозитории и обновляет проект.
    """
    # print(request.json)
    cmd = 'echo "kek" > lol.kek'
    os.system(cmd)
    # cmd = 'sudo touch lol.kek'
    cmd = 'sudo ./update.sh'
    os.system(cmd)
    print(cmd)
    # return jsonify(success=True, data=request.json)
    return str(request.json)


@app.route('/update_table_players', methods=['POST'])
def update_table_players() -> jsonify:
    """
    Функция для обновления таблицы игроков данными, полученными через POST-запрос.
    Эта функция добавляет нового игрока в таблицу players, используя его полное имя (fio) и идентификатор игрока.
    В случае успешного выполнения возвращает JSON-ответ с сообщением об успехе, в противном случае возвращает сообщение об ошибке.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    try:
        print(request.json)
        d = request.json
        print(type(d))
        fio = d['playerFIO']
        player_id = d['playerName']

        query = 'insert into players (fio, player_id) values (?, ?)'
        cursor.execute(query, (fio, player_id))
        db_connection.commit()

        response = {"success": True}
        return jsonify(response)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.errorhandler(404)
def page_not_found(error):
    """Отображает страницу ошибки в случае перехода на несуществующую страницу."""
    return render_template('404.html', error=error), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)
    # app.run(debug=True)
