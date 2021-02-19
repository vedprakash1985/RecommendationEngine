# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 18:33:51
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-19 13:48:23


# Main class to read the DB and obtain processed dataframe
import sqlite3
import pandas as pd


class DB: 
	def __init__(self, filename, top =10):
		"""
		Args:
			filename (str): D
			top (int, optional): Description
		"""
		self.top = 10

		# Create the connection to DB
		self.conn = sqlite3.connect(filename)


	def getTopUsers(self): 
		"""
		Get the top users 
		This is based on checkins, but home town location is dropped, 
		i.e. a check-in is valid only when not in home-town, based on lat long coordinates
		
		Returns:
			topusers (list): Contains the ids of the top users
		"""

		query = """select M.user_id, count( distinct M.venue_id) as cnt
					from
					(
					select J.user_id, J.venue_id, J.latitude, J.longitude, J.Homelat, J.Homelong,
					CASE
						WHEN J.latitude = J.Homelat and J.longitude = J.Homelong THEN 1
						ELSE 0
						END bool
					from 
					(
					select C.*, U.latitude as Homelat, U.longitude as Homelong 
					from checkins C
					left join users U
					on U.id = C.user_id
					) J
					where bool=0
					) M
					group by user_id
					order by cnt desc, user_id
					limit {}""".format(self.top)

		df = pd.read_sql_query(query, self.conn)

		topusers = df["user_id"].tolist()

		return topusers

	def getrating(self):
		"""
		Get the user id and all ratings of all places visited.
		For cases where user gives multiple ratings to the same venue, the average of these ratings is used. 
		Returns:
		    df (pandas dataframe): 
		"""

		query = """select C.user_id, C.venue_id , R.Rating
					from 
					(
					select user_id, venue_id, max(created_at)
					from checkins
					group by user_id, venue_id) C
					left join
					(
					select user_id, venue_id, avg(rating) as Rating from ratings 
					group by user_id, venue_id
					) R
					where  C.user_id = R.user_id and C.venue_id  = R.venue_id"""

		df = pd.read_sql_query(query, self.conn)

		# TODO: Convert to matrix 

		return df

	def close(self):
		"""
		Close the connection
		"""

		self.conn.close()
