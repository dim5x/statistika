def create_tables(db_connection):
    print('Function create_tables() called...')
    query = '''
                create table if not exists players
                (
                id integer primary key autoincrement,
                fio text not null,
                player_id text not null
                );

                create table if not exists teams
                (
                    id integer primary key autoincrement,
                    name text not null
                );


                create table if not exists games
                (
                    id integer primary key autoincrement,
                    games_date date not null
                );

                create table if not exists game_result
                (
                    game_id integer,
                    game_type text,
                    team_id integer,
                    team_score integer
                );

                create table if not exists scores
                (
                    position integer,
                    score integer
                );

                create view game_scores as
                select 
                    team_name,
                    cast(games_date as text) games_date,
                    team_score,
                    game_type,
                    ifnull(round(avg(case 
                                --when team_score is not null and score is not null then score
                                when team_score is not null and score is null then 0
                                else score 
                            end) over(partition by games_date, game_type, pos2),2),0) _score
                from 
                    (
                    select 
                        games.date games_date,
                        teams.name team_name,
                        team_score,
                        game_type,
                        case 
                            when team_score is not null then row_number() over(partition by games.date, game_type order by team_score desc) 
                            else -1
                        end pos,
                        case 
                            when team_score is not null then rank() over(partition by games.date, game_type order by team_score desc) 
                            else -1
                        end pos2
                    from
                        game_result
                        join
                        teams
                        on
                        game_result.team_id = teams.id
                        join
                        games 
                        on
                        game_result.game_id = games.id
                    ) _data
                    left join
                    scores
                    on
                    _data.pos = scores.position
                '''
    cursor = db_connection.cursor()
    cursor.executescript(query)
    db_connection.commit()


def load_test_data(db_connection):
    query = '''
            delete from teams;

            insert into teams(name) values
                ('Old School'),
                ('Бутылка брома'),
                ('Мимо проходили'),
                ('Один за всех и все за Одина'),
                ('Дети капитана Марвела'),
                ('Паровозик, который смог'),
                ('Золотая шобла'),
                ('Серп и молот Тора');

            delete from players;

            insert into players(fio, player_id) values
                ('Леонов Александр', 59778),
                ('Чечекин Максим', 172423),
                ('Вишнякова Наталья', 172425),
                ('Лебедев Алексей', 53716),
                ('Солопов Максим', 172528),
                ('Бадмаева Ирина', 94023),
                ('Гизатуллин Олег', 47697);

            delete from games;

            insert into games(date) values
                ('2024-03-07'),
                ('2024-03-14'),
                ('2024-03-21'),
                ('2024-03-28'),
                ('2024-04-04'),
                ('2024-04-11'),
                ('2024-04-18');

            delete from game_result;

            insert into game_result(game_id, game_type, team_id, team_score) values
                (1, 'ЧГК', '1', 18),
                (1, 'ЧГК', '2', 16),
                (1, 'ЧГК', '3', null),
                (1, 'ЧГК', '4', 12),
                (1, 'ЧГК', '5', 16),
                (1, 'ЧГК', '6', 14),
                (1, 'ЧГК', '7', null),
                (1, 'ЧГК', '8', null),
                (2, 'ЧГК', '1', 24),
                (2, 'ЧГК', '2', 21),
                (2, 'ЧГК', '3', 15),
                (2, 'ЧГК', '4', 21),
                (2, 'ЧГК', '5', 19),
                (2, 'ЧГК', '6', 25),
                (2, 'ЧГК', '7', null),
                (2, 'ЧГК', '8', null),
                (3, 'ЧГК', '1', 20),
                (3, 'ЧГК', '2', 18),
                (3, 'ЧГК', '3', 16),
                (3, 'ЧГК', '4', 21),
                (3, 'ЧГК', '5', 22),
                (3, 'ЧГК', '6', 25),
                (3, 'ЧГК', '7', null),
                (3, 'ЧГК', '8', 15),
                (4, 'ЧГК', '1', 22),
                (4, 'ЧГК', '2', 14),
                (4, 'ЧГК', '3', 16),
                (4, 'ЧГК', '4', 20),
                (4, 'ЧГК', '5', 17),
                (4, 'ЧГК', '6', 26),
                (4, 'ЧГК', '7', null),
                (4, 'ЧГК', '8', null),
                (5, 'ЧГК', '1', 18),
                (5, 'ЧГК', '2', 12),
                (5, 'ЧГК', '3', 18),
                (5, 'ЧГК', '4', 23),
                (5, 'ЧГК', '5', 19),
                (5, 'ЧГК', '6', 22),
                (5, 'ЧГК', '7', 15),
                (5, 'ЧГК', '8', null),
                (6, 'ЧГК', '1', 15),
                (6, 'ЧГК', '2', null),
                (6, 'ЧГК', '3', 9),
                (6, 'ЧГК', '4', 20),
                (6, 'ЧГК', '5', 13),
                (6, 'ЧГК', '6', 18),
                (6, 'ЧГК', '7', 12),
                (6, 'ЧГК', '8', null),
                (7, 'ЧГК', '1', 19),
                (7, 'ЧГК', '2', 15),
                (7, 'ЧГК', '3', 10),
                (7, 'ЧГК', '4', 19),
                (7, 'ЧГК', '5', 18),
                (7, 'ЧГК', '6', 19),
                (7, 'ЧГК', '7', null),
                (7, 'ЧГК', '8', null);

                delete from scores;

                insert into scores(position,score) values
                (1, 10),
                (2, 7),
                (3, 5),
                (4, 3),
                (5, 2),
                (6, 1);

            '''
    cursor = db_connection.cursor()
    cursor.executescript(query)
    db_connection.commit()
