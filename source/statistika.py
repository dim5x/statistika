import json
import os
import sqlite3
import subprocess
import sys
sys.path.append('cicd')
import db_initialization
import db_management

from flask import Flask, render_template, request, jsonify, g, redirect
from flask_cors import CORS  # pip install flask_cors

# from typing import List

app = Flask(__name__)
CORS(app)


def get_db_connection() -> sqlite3.Connection:
    """
    Функция, которая получает соединение с базой данных.
    Если соединение не существует, устанавливает новое соединение с использованием SQLite с 'data.db'.
    Возвращает существующее или новосозданное соединение с базой данных.
    """

    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        #для тестирования
        #os.remove('../data.db')
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
@app.route('/maintable')
def maintable() -> str:
    """
    Функция, которая служит обработчиком маршрута для корневого URL. Отображает шаблон 'index.html'.
    """
    print('kek')

    # return render_template('index.html')
    return render_template('maintable.html')


@app.route('/add_game', methods=['GET'])
def add_game() -> str:
    return render_template('add_game.html')


@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    return render_template('add_player.html')


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
            'hozAlign': 'center' if column == 'summa_2' else 'left'
        })

    # Вывод преобразованных объектов
    # print(f'{transformed_columns=}')
    print(transformed_columns)
    return jsonify(transformed_columns)


@app.route('/get_data_for_main_table', methods=['GET'])
def get_data_for_main_table() -> list[dict[str, any]]:
    """
    Функция для извлечения данных для основной таблицы из базы данных SQLite и возврата их в формате JSON.
    """
    db_connection = get_db_connection()
    data = db_management.get_maintable(db_connection)

    # Получение названий столбцов из результирующего набора
    columns = [description[0] for description in data.description]
    print(columns)

    # Преобразование данных в формат JSON
    json_data = []
    for row in data:
        row_data = {}
        for i in range(0, len(columns)):
            row_data[columns[i]] = row[i]
        json_data.append(row_data)
    # print(data)
    return json_data
    # return jsonify(data)


@app.route('/get_data_for_table_players', methods=['GET'])
def get_data_for_table_players() -> list[dict[str, any]]:
    """
    Получить данные для таблицы игроков и вернуть их в виде JSON объекта.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute('SELECT * FROM main.players')  # Выберите все столбцы из таблицы players
    data = cursor.fetchall()

    columns = [description[0] for description in cursor.description]
    # print(columns)

    json_data = []
    for row in data:
        row_data = {}
        for i in range(len(columns)):
            row_data[columns[i]] = row[i]
        json_data.append(row_data)
    # print(json_data)
    return (json_data)


@app.route('/get_data_for_table_teams', methods=['GET'])
def get_data_for_table_teams() -> list[dict[str, str]]:
    """
    Функция для получения данных для таблицы команд. Она подключается к базе данных, извлекает названия команд,
    структурирует данные в список словарей и возвращает данные.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute(
        '''
        select 
            name 
        from
            teams
        ''')  # Выберите все столбцы из таблицы players
    data = []
    for i in cursor.fetchall():
        data.append({'Name': i[0]})  # data.append(i[0])

    # print()
    print(type(data))
    print(f'FROM main.teams_scores: {data=}')
    # return jsonify(success=True, data=data)
    return data


@app.route('/check_packet', methods=['POST'])
def check_packet() -> jsonify:
    """
    Функция для проверки пакетов и извлечения информации об игроках для каждого идентификатора турнира.
    Эта функция взаимодействует с базой данных, чтобы извлечь данные об игроках и сопоставить их с идентификаторами турниров.
    Возвращает JSON-ответ с успешным статусом и данными, содержащими информацию об игроках для каждого турнира.
    """
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    print('lol')
    # print(request.json)

    query = "SELECT player_id, fio FROM main.players"
    players_data = cursor.execute(query).fetchall()
    # players_set = set([player[0] for player in players_data])
    players_dict = {k: v for k, v in players_data}
    # print(f'{players_dict=}')

    answer = []
    for tour_id in request.json:
        # print(f'{tour_id=}')
        if tour_id:
            query = 'SELECT player_id from tournaments WHERE tournaments.tournament_id = ?'
            tournaments_player_id = cursor.execute(query, (int(tour_id),)).fetchall()
            # print(f'{tournaments_player_id=}')
            if not tournaments_player_id:
                answer.append(f'Турнир {tour_id} в базе не найден.<br>')
                continue
            tournaments_player_id_set = set(tournaments_player_id[0][0].split(';'))
            # print(f'{tournaments_player_id_set=}')
            intersection = tournaments_player_id_set.intersection(players_dict.keys())

            # https: // rating.maii.li / b / player / 172423 /
            if intersection:
                # print(f'{intersection=}')
                # for j in intersection:
                #     url = f'<a href="https://rating.maii.li/b/player/{j}>{players_dict[j]}</a>'
                #     answer.append(f'В турнире {tour_id} играл(и): {url}')
                answer.append(f'В турнире {tour_id} играл(и): {[players_dict[i] for i in intersection]}<br>')
            else:
                answer.append(f'В турнире {tour_id} никто не играл.')
            # print(f'{answer=}')
            # print('\n'.join(answer))
    return jsonify(success=True, data=''.join(answer))


@app.route('/set_result', methods=['POST'])
def set_result():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    # print('result')
    # print(request.json)

    # Получение названий всех колонок
    cursor.execute("PRAGMA table_info(teams_scores)")
    columns = [info[1] for info in cursor.fetchall()]

    # Определение колонок для суммирования (те, что имеют формат даты)
    date_columns = [col for col in columns if "-" in col]

    # Создание части запроса для суммирования значений этих колонок
    sum_expression = " + ".join([f'COALESCE("{col}", 0)' for col in date_columns])

    # Создание части запроса для суммирования значений этих колонок без двух наименьших значений
    sum_minus_two_least_expression = f"""
        SELECT ({sum_expression}) -
        COALESCE((SELECT SUM(val) FROM (
            SELECT val FROM (
                SELECT {', '.join([f'COALESCE("{col}", 0)' for col in date_columns])} AS val
                FROM main."teams_scores-mark_for_deletion" t2
                WHERE t2.id = teams_scores.id AND t2.team_name NOT LIKE '%_q%'
            )
            ORDER BY val LIMIT 2
        )), 0)
        FROM main."teams_scores-mark_for_deletion" t3
        WHERE t3.id = teams_scores.id AND t3.team_name NOT LIKE '%_q%'
    """
    # print(f'{sum_minus_two_least_expression=}')
    # Генерация полного SQL-запроса для обновления
    sql_update_query = f"""
    UPDATE main."teams_scores-mark_for_deletion"
    SET summa = (
        SELECT {sum_expression}
        FROM main."teams_scores-mark_for_deletion" t2
        WHERE t2.id = "teams_scores-mark_for_deletion".id AND t2.team_name NOT LIKE '%_q%'
    ),
    summa_2 = (
        {sum_minus_two_least_expression}
    )
    WHERE team_name NOT LIKE '%_q%';
    """

    # Выполнение SQL-запроса
    cursor.execute(sql_update_query)
    db_connection.commit()

    # Закрытие соединения
    # conn.close()

    # query = "SELECT player_id, fio FROM main.players"
    # players_data = cursor.execute(query).fetchall()
    # # players_set = set([player[0] for player in players_data])
    # players_dict = {k: v for k, v in players_data}
    # # print(f'{players_dict=}')
    #
    # answer = []
    # for i in request.json:
    #     # print(f'{i=}')
    #     if i:
    #         query = 'SELECT player_id from tournaments WHERE tournaments.tournament_id = ?'
    #         tournaments_player_id = cursor.execute(query, (int(i),)).fetchall()
    #         print(f'{tournaments_player_id=}')
    #         if not tournaments_player_id:
    #             answer.append(f'Турнир {i} в базе не найден.')
    #             continue
    #         tournaments_player_id_set = set(tournaments_player_id[0][0].split(';'))
    #         print(f'{tournaments_player_id_set=}')
    #         intersection = tournaments_player_id_set.intersection(players_dict.keys())
    #
    #         # https: // rating.maii.li / b / player / 172423 /
    #         if intersection:
    #             answer.append(f'В турнире {i} играл(и): {[players_dict[i] for i in intersection]}')
    #         else:
    #             answer.append(f'В турнире {i} никто не играл.')
    # print(f'{answer=}')
    # print('\n'.join(answer))
    # return jsonify(success=True, data='\n'.join(answer))
    return jsonify(success=True, data=request.json)


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555)
    # app.run(debug=True)
