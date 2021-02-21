# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 18:33:51
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-21 22:02:53


# Main class to read the DB and run SQL queries
import sqlite3
import pandas as pd
import numpy as np
from scipy.sparse import lil_matrix


class DB: 
	def __init__(self, filename, top =10):
		"""
		Args:
			filename (str): Local path of DB
			top (int, optional): Description
		"""
		self.top = top

		# Create the connection to DB
		self.conn = sqlite3.connect(filename)

		# Get the top users
		self.getTopUsers()


	def getTopUsers(self): 
		"""
		Get the top users 
		This is based on checkins, but home town locations are dropped, 
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

		self.topusers = df["user_id"].tolist()

	def getSocialUsers(self):
		"""
		Get the user_ids of the social users, from the unvierse of ids who have visited at least one place.

		Returns:
		    topSocialusers (list): User-ids of the social users
		"""
		query = """select first_user_id as user_id, count(distinct second_user_id) as cnt  from socialgraph
						where first_user_id in (select distinct user_id from checkins)
						group by first_user_id
						order by cnt desc
						limit {}""".format(self.top)

		df = pd.read_sql_query(query, self.conn)

		topSocialusers = df["user_id"].tolist()

		return topSocialusers

	def getcheckinsSocialUsers(self, topSocialusers, start_date):
		"""
		Get the venues visited by a set of users from start_date

		Args:
		    topSocialusers (list): User_id of the users who we need the venue which they have visited
		    start_date (str): 'YYYY-MM-DD' date format
		
		Returns:
		    df (pd.DataFrame): The venue_ids of the places visited by the users, together with the  (lat,long) coordinates
		"""
		d = {}
		d["start"] = start_date
		d["socialusers"] = tuple(topSocialusers)

		query = """select * from checkins
					where created_at >= '{start}'
					and user_id in {socialusers}""".format(**d)


		df = pd.read_sql_query(query, self.conn)

		return df

	def getFriends(self, users):
		"""
		Get all the friends of users
		
		Args:
		    users (tuple): user_id of users to get friends
		
		Returns:
			df (pd.DataFrame): First column is the user_id, second column is the user_id of the friend.
		"""

		query = """select * from socialgraph
					where  first_user_id in {}
					group by first_user_id, second_user_id""".format(users)

		df = pd.read_sql_query(query, self.conn)

		return df

	def getVenueIds(self, users):
		"""
		Get all the venues visited by users
		
		Args:
		    users (tuple): user id of users
		
		Returns:
		    df (pd.DataFrame): First column is the user_id, second column is the venue_id of the place visited
		"""

		query = """select user_id, venue_id from checkins
					where user_id in {}
					group by user_id, venue_id""".format(users)

		df = pd.read_sql_query(query, self.conn)

		return df



	def getrating(self):
		"""
		Get the user id and all ratings of all places visited.
		For cases where user gives multiple ratings to the same venue, the average of these ratings is used. 

		Returns:
			df (pandas dataframe): Columns are user_id, venue_id and (Average) Rating
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

		return df

	def getSocialNetwork(self):
		"""
		Get the friends of all top users with their weights
		
		Returns:
			df (pandas dataframe): Columns are top_user_id, friend_id, weight
		"""

		query = """select first_user_id as top_user_id, second_user_id as friend_id, count(*) 
						as weight from socialgraph
						where first_user_id in {}
						group by first_user_id, second_user_id""".format(tuple(self.topusers))

		df = pd.read_sql_query(query, self.conn)

		return df

	def getUserItemMatrix(self):
		"""
		Get the user-item sparse matric
		
		Returns:
			[d_map, X] (dict, scipy.sparse.csr.csr_matrix)
				1) d_map is the dictionary of row and column mappings for matrix X
					To get rating of user u for venue v, use the following
					X[d_map["row"][u], d_map["col"][v]]
		"""
		df = self.getrating()

		rows_index = df.user_id.unique()
		column_index = df.venue_id.unique() 

		row_len = len(rows_index)
		col_len = len(column_index)

		X = lil_matrix((row_len, col_len))
		row_map = dict(zip(rows_index, range(row_len)))
		col_map = dict(zip(column_index, range(col_len)))

		#  Get mapping table for rows and columns
		d = {}
		d["row"] = row_map
		d["col"] = col_map

		for index, row in df.iterrows():
			X[d["row"][row["user_id"]], d["col"][row["venue_id"]]] = row["Rating"]

		X = X.tocsr()  # Allow efficient row slicing

		return [d,X]


	def getSocialSimilarityMatrix(self, column_map):
		"""
		Get the similarity matrix based on the social network graph for the top users.

		Args:
		    column_map (dict): Mapping of users to index of S

		Returns:
		    S (scipy.sparse.csr.csr_matrix): Similarity matrix, Size k x n, where
		    	i) k is the number of top users
		    	ii) n is the total number of users in the given universe
		

		"""

		df = self.getSocialNetwork()

		S = lil_matrix((len(self.topusers), len(column_map)))

		for index, row in df.iterrows():
			if row["friend_id"] in column_map.keys():
				S[ self.topusers.index(row["top_user_id"]), column_map[row["friend_id"]] ] = row["weight"]
			else:
				pass
				# print("User %i did not make any checkins" %row["friend_id"] )

		for i in range(len(self.topusers)):
			S[i, column_map[self.topusers[i]]]  = S[i, column_map[self.topusers[i]]]  +1

		S = S.tocsr()

		return S

	def close(self):
		"""
		Close the connection
		"""

		self.conn.close()
