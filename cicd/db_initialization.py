import source.statistika_logger

log = source.statistika_logger.get_logger(__name__)


def create_tables(db_connection):
    log.warning('Creating tables...')
    query = '''
                create table if not exists players
                (
                    id integer primary key autoincrement,
                    fio text not null,
                    player_id text not null,
                    team_id integer,
                    tournaments text
                );

                create table if not exists teams
                (
                    id integer primary key autoincrement,
                    name text not null
                );


                create table if not exists games
                (
                    id integer primary key autoincrement,
                    date date not null
                );

                create table if not exists game_result
                (
                    game_id integer,
                    game_type text,
                    team_id integer,
                    team_score integer default null
                );

                create table if not exists scores
                (
                    position integer,
                    score integer
                );

                create table if not exists users
                (
                    login text,
                    salt text,
                    hash text
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
    log.warning('Loading test data...')
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

            insert into players(fio, player_id, team_id, tournaments) values
                ('Леонов Александр', 59778, 5, '1635,1725,1726,1750,1806,1845,1849,1854,2019,2026,2031,2158,2246,2357,2424,2535,2556,2557,2578,2585,2689,2695,2708,2742,2749,2757,2778,2783,2789,2817,2856,2858,4112,4311,6248,6349,8526,8451,8312,8440,8285,8442,7884,8325,7700,8444,8311,8621,8645,7702,8631,8734,8839,7706,8873,8309,8993,8953,8842,9094,8897,9033,8841,9070,9196,9395,9074,9388,9520,9858,9860,9609,9869,9205,9721,9737,9938,9693,9207,9695,9425,9427,9739,9850,10179'),
                ('Чечекин Максим', 172423, 4,'4705,4790,4883,4946,4965,4970,4971,4974,4975,4981,4982,4983,4984,4985,4986,5030,5076,5096,5102,5107,5109,5118,5213,5310,5367,5397,5433,5437,5504,5509,5512,5516,5518,5559,5591,5611,5676,5719,5725,5727,5728,5729,5730,5751,5752,5753,5754,5760,5764,5770,5784,5794,5818,5820,5821,5822,5823,5824,5913,6041,6042,6228,6255,6667,6669,6670,6671,6752,6753,6963,7068,7105,7122,7138,7189,7242,7249,7250,7293,7368,7370,7412,7372,6841,7251,7374,7252,7682,7253,7736,7873,7468,7891,7887,7261,8024,7974,8119,8140,8022,8083,8151,8249,8234,8268,8300,8364,8272,8450,7696,7689,8312,8583,7698,7700,8444,8645,7702,8631,8747,7704,8673,8676,8422,8778,8734,8839,7706,8873,8309,8993,8953,8842,9014,8897,9033,8841,9070,9196,9395,9074,9388,9126,9438,9193,9501,9247,9402,9520,9528,9858,9860,9550,9203,9609,9287,9205,9423,9693,9425,9632,9815,9850,9211,9653,9588,9663,9539,9213,9590,10179,9592,9657,9757,9673,10615,10616,9661'),
                ('Вишнякова Наталья', 172425, 4, '4705,4790,4883,4946,4965,4969,4981,4983,4984,4985,5030,5096,5102,5109,5213,5367,5397,5433,5437,5504,5509,5512,5518,5559,5610,5611,5675,5718,5719,5725,5727,5728,5730,5752,5760,5764,5770,5784,5794,5821,5822,5823,6041,6255,6669,6670,6671,6676,6752,6753,6963,7068,7105,7122,7138,7145,7189,7206,7242,7249,7250,7293,7370,7412,6841,7251,7374,7576,7417,7252,7682,7253,7228,7736,7873,7468,7925,7891,7887,7935,8024,7194,7725,8088,8119,8068,8140,8204,8022,8083,7791,8151,8249,8234,8268,8313,8322,8260,8364,8450,7696,7689,8312,8583,8583,8525,8646,8645,7702,8747,8747,7704,8633,8673,8676,8422,8778,8734,8692,8839,7706,8856,9094,9014,8897,9068,8849,9072,9395,9126,9438,9193,9501,9247,9402,9547,9520,9528,9541,9858,9860,9550,9203,9609,9205,9423,9364,9632,9815,9211,9653,10287,9663,10293,9973,9711,9213,9671,9590,10179,9592,9657,9757,10616,9597,10619'),
                ('Лебедев Алексей', 53716, 4, '1652,7261,8022,8300,8272,8450,8312,7698,7700,8502,7704,8873,8309,9094,9528,9860,9550,9632,9211,10293,10615,10619,10747'),
                ('Солопов Максим', 172528, 4, '4705,4969,4970,4971,4972,4974,4981,4982,4983,4984,4985,4986,5076,5102,5107,5109,5118,5213,5310,5397,5433,5437,5509,5518,5591,5610,5718,5719,5725,5727,5730,5751,5752,5753,5754,5760,5764,5770,5784,5794,5820,5821,5822,5823,5913,6042,6228,6255,6671,6752,7068,7138,7189,7242,7249,7250,7368,7370,7374,7252,7682,7253,7736,7873,7468,7925,7887,7261,7974,8119,8022,8151,8234,8300,7696,8312,8583,7698,7700,8444,8631,8747,8676,8778,8734,7706,8993,8953,8842,9014,8897,9033,8841,9196,9388,9126,9438,9193,9501,9247,9520,9528,9858,9860,9550,9205,9425,9632,9209,9850,9588,9663,9539,10293,9213,9590,9592,9657,9757,9673,9659,10617,10619,9661,10453'),
                ('Бадмаева Ирина', 94023, 5, '2557,2578,2585,2708,2742,2749,2757,2817,2856,2858,4112,8422,8309'),
                ('Гизатуллин Олег', 47697,5, '640,664,689,1687,1845,1854,2019,2026,2031,2158,2246,2357,2556,2578,2689,2695,2708,2742,2749,2757,2783,2789,2817,2856,2858,5052,5056,5071,5205,5207,5370,5444,5491,5504,5563,6248,9528,9727,9541,9550');

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

                insert into scores(position, score) values
                (1, 10),
                (2, 7),
                (3, 5),
                (4, 3),
                (5, 2),
                (6, 1);

                delete from users;
                insert into users(login, salt, hash) values
                ('admin', '8b9dbd971866baf5f09e7bf6557ee6a047eddc394bb2e685ef2b2c38fbb38e18c10c5c568155a6b41db18090617eabcee856c0f7439af84cb3307892f0fb322f',
                '2e74791e8816226fcc3eb0b82173ee525dc4989cedc8cba24f73aafa5abc8da7294b2fee8e174a0de6a7cbdb447da916dadfe21bc0516c2788428fa1529b6d07');

            '''
    cursor = db_connection.cursor()
    cursor.executescript(query)
    db_connection.commit()
