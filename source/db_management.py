import sqlite3

def get_maintable(db_connection):
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