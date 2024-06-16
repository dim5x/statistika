import sqlite3
def get_maintable(db_connection: sqlite3.Connection) -> sqlite3.Cursor:
    """
    Получаем основную таблицу для указанного соединения с базой данных.

    Аргументы:
        db_connection (sqlite3.Connection): Объект соединения с базой данных.
    """

    query = '''
            with 
                    games as 
                    (
                    select 
                        '_sum_'  games_date,
                        1 _order
                      union all
                      select 
                        '_sum_minus_2' games_date,
                        2
                      union all
                      select distinct 
                        games_date games_date,
                        3
                      from 
                        game_scores 
                      order by 
                        _order,
                        games_date
                    ),
                    lines as 
                    (
                    select 
                        'select team_name ' as part
                    union all
                    select 
                        ', sum(_score) filter (where games_date = "' || games_date || '") as "' || games_date || '" '
                    from 
                        games 
                    union all
                    select 
                        'from (
                                select
                                    *
                                from
                                    game_scores
                                union
                                select 
                                    team_name,
                                    "_sum_",
                                    null,
                                    game_type,
                                    sum(_score)
                                from 
                                    (
                                    select 
                                        *,
                                        count(1) over(partition by team_name, game_type) count_games,
                                        row_number() over(partition by team_name, game_type order by _score desc) _row
                                    from 
                                        game_scores
                                    ) d
                                group by
                                    team_name,
                                    game_type
                                union 
                                select 
                                    team_name,
                                    "_sum_minus_2",
                                    null,
                                    game_type,
                                    sum(_score) filter (where count_games - _row >= 2)
                                from 
                                    (
                                    select 
                                        *,
                                        count(1) over(partition by team_name, game_type) count_games,
                                        row_number() over(partition by team_name, game_type order by _score desc) _row
                                    from 
                                        game_scores
                                    ) d
                                group by
                                    team_name,
                                    game_type
                                ) 
                        group by 
                                team_name 
                        order by 
                                team_name;'
                )
                select 
                    group_concat(part, '')
                from 
                    lines
                    limit 1;
    '''
    cursor = db_connection.cursor()
    cursor.execute(query)
    query = cursor.fetchone()[0]
    data = cursor.execute(query)
    return data


def get_players(db_connection):
    cursor = db_connection.cursor()
    # query = 'SELECT * FROM main.players'
    query = ('SELECT fio, player_id, teams.name '
             'FROM main.players, main.teams '
             'WHERE players.team_id = teams.id')
    cursor.execute(query)  # Выберите все столбцы из таблицы players
    data = cursor.fetchall()
    return data


def get_teams(db_connection):
    cursor = db_connection.cursor()
    query = 'SELECT name FROM main.teams'
    cursor.execute(query)  # Выберите все столбцы из таблицы teams
    data = cursor.fetchall()
    return data


def update_main_table(db_connection, json, date):
    cursor = db_connection.cursor()
    query = 'INSERT INTO main.games(date) VALUES (?)'
    cursor.execute(query, (date,))
    db_connection.commit()

    game_id = cursor.lastrowid

    # Получить словарь команд
    teams_query = 'SELECT id, name FROM main.teams'
    cursor.execute(teams_query)
    teams = {team[1]: team[0] for team in cursor.fetchall()}
    # print(teams)

    # Заменить название команды на ID команды в json
    json_with_team_ids = [(game_id, 'ЧГК', teams[row], None if json[row] == '' else json[row]) for row in json]

    query = 'INSERT INTO main.game_result(game_id, game_type, team_id, team_score) VALUES (?, ?, ?, ?)'
    cursor.executemany(query, json_with_team_ids)
    db_connection.commit()
    return
