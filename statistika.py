import json
import sqlite3

from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS  # pip install flask_cors

app = Flask(__name__)
CORS(app)
players = [[1, 'test', 78], [2, 'test2', 145], [3, 'test3', 23], [4, 'test4', 45]]

rows = [
    [1, 2, 3, 4, 1, 2, 3, 4, 7],
    [1, 2, 3, 4, 1, 2, 3, 4, 7],
    [1, 2, 3, 4, 1, 2, 3, 4, 7],
    [1, 2, 3, 4, 1, 2, 3, 4, 7],
]


def get_db_connection():
    db_connection = getattr(g, '_database', None)
    if db_connection is None:
        db_connection = g._database = sqlite3.connect('data.db')
    return db_connection


@app.teardown_appcontext
def close_db_connection(exception):
    db_connection = getattr(g, '_database', None)
    if db_connection is not None:
        db_connection.close()


@app.route('/')
def index():
    print('kek')

    return render_template('index.html')


@app.route('/get_columns', methods=['GET'])
def get_columns():
    # Подключение к базе данных SQLite
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    # Выполнение SQL-запроса и получение данных
    cursor.execute('SELECT * FROM main.teams_scores')  # Выберите все столбцы из таблицы players
    data = cursor.fetchall()

    # Получение названий столбцов из результирующего набора
    columns = [description[0] for description in cursor.description]
    print(f'{columns=}')
    transformed_columns = []

    # Цикл для преобразования каждого элемента массива строк в объект
    for column in columns[1:]:
        if column == "Сумма_2":
            transformed_columns.append({
                "title": column,
                "field": column,
                "editor": "input",
                "sorter": "number",
                'hozAlign': "center",

            })
            continue
        transformed_columns.append({
            "title": column,
            "field": column,
            "editor": "input",  # if column == "team_name" else "number"
            # Пример условной логики для определения значения editor

        })

    # Вывод преобразованных объектов
    print(f'{transformed_columns=}')
    return jsonify(transformed_columns)


@app.route('/packet', methods=['POST'])
def packet():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    print('lol')
    print(request.json)

    query = "SELECT player_id, fio FROM main.players"
    players_data = cursor.execute(query).fetchall()
    # players_set = set([player[0] for player in players_data])
    players_dict = {k: v for k, v in players_data}
    # print(f'{players_dict=}')

    answer = []
    for tour_id in request.json:
        print(f'{tour_id=}')
        if tour_id:
            query = 'SELECT player_id from tournaments WHERE tournaments.tournament_id = ?'
            tournaments_player_id = cursor.execute(query, (int(tour_id),)).fetchall()
            print(f'{tournaments_player_id=}')
            if not tournaments_player_id:
                answer.append(f'Турнир {tour_id} в базе не найден.<br>')
                continue
            tournaments_player_id_set = set(tournaments_player_id[0][0].split(';'))
            print(f'{tournaments_player_id_set=}')
            intersection = tournaments_player_id_set.intersection(players_dict.keys())

            # https: // rating.maii.li / b / player / 172423 /
            if intersection:
                print(f'{intersection=}')
                # for j in intersection:
                #     url = f'<a href="https://rating.maii.li/b/player/{j}>{players_dict[j]}</a>'
                #     answer.append(f'В турнире {tour_id} играл(и): {url}')
                answer.append(f'В турнире {tour_id} играл(и): {[players_dict[i] for i in intersection]}<br>')
            else:
                answer.append(f'В турнире {tour_id} никто не играл.')
            print(f'{answer=}')
            print('\n'.join(answer))
    return jsonify(success=True, data=''.join(answer))


@app.route('/result', methods=['POST'])
def result():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    print('result')
    print(request.json)

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
                FROM main.teams_scores t2
                WHERE t2.id = teams_scores.id AND t2.team_name NOT LIKE '%_q%'
            ) 
            ORDER BY val LIMIT 2
        )), 0)
        FROM main.teams_scores t3
        WHERE t3.id = teams_scores.id AND t3.team_name NOT LIKE '%_q%'
    """
    print(f'{sum_minus_two_least_expression=}')
    # Генерация полного SQL-запроса для обновления
    sql_update_query = f"""
    UPDATE main.teams_scores
    SET Сумма = (
        SELECT {sum_expression}
        FROM main.teams_scores t2
        WHERE t2.id = teams_scores.id AND t2.team_name NOT LIKE '%_q%'
    ),
    Сумма_2 = (
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


@app.route('/get_data_for_main_table', methods=['GET'])
def get_data_for_main_table():
    # Подключение к базе данных SQLite
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    # Выполнение SQL-запроса и получение данных
    cursor.execute('SELECT * FROM main.teams_scores')  # Выберите все столбцы из таблицы players
    data = cursor.fetchall()

    # Получение названий столбцов из результирующего набора
    columns = [description[0] for description in cursor.description]
    print(columns)

    # Преобразование данных в формат JSON
    json_data = []
    for row in data:
        if '_q' not in row[1]:
            row_data = {}
            for i in range(1, len(columns)):
                row_data[columns[i]] = row[i]
            json_data.append(row_data)
    print(json_data)
    # Вывод данных в формате JSON
    print(json.dumps(json_data, indent=2, ensure_ascii=False))
    # json_data = json.dumps([
    #     {
    #         "id": 16,
    #         "team_name": "Золотая_шобла_r",
    #         "Игра": '0',
    #         "[14.03.2024]": 0,
    #         "21.03.2024": 0,
    #         "28.03.2024": 0,
    #         "04.04.2024": 1,
    #         "11.04.2024": 2,
    #         "18.04.2024": 0
    #     }
    # ], indent=2, ensure_ascii=False)
    return json_data


@app.route('/get_data_for_table_players', methods=['GET'])
def get_data_for_table_players():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute('SELECT * FROM main.players')  # Выберите все столбцы из таблицы players
    data = cursor.fetchall()

    columns = [description[0] for description in cursor.description]
    print(columns)

    json_data = []
    for row in data:
        row_data = {}
        for i in range(len(columns)):
            row_data[columns[i]] = row[i]
        json_data.append(row_data)
    print(json_data)
    return json_data


@app.route('/test', methods=['POST', 'GET'])
def test():
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


@app.route('/update', methods=['POST'])
def update():
    """
    Update a specific cell in the dataframe with the provided value.

    This function is an endpoint for a POST request to '/update'. It expects the request to contain the following
    parameters:
    - row_id: The index of the row to update.
    - column_id: The name of the column to update.
    - value: The new value to set in the specified cell.
"""

    try:
        row_id = int(request.form['row_id'])
        column_id = int(request.form['column_id'])
        value = request.form['value']
        print('lol')
        # print(f"Received data - row_id: {row_id}, column_id: {column_id}, value: {value}")

        # Update the dataframe
        # data.at[row_id, column_name] = value
        # print(data)
        # # Save back to CSV
        # data.to_csv('data.csv', index=False, header=False)

        return jsonify(success=True)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


@app.route('/update_table_players', methods=['POST'])
def update_table_players():
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
