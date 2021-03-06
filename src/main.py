# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 10:48:30
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-21 22:01:42

# Main Script to run for Questions 1 and 2 in Outline of readme file

import pandas as pd 
import argparse
import json
import numpy as np
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity

# Import from local modules
from DB import DB



def savedisk(d_venue, loc):
	"""
	Save the recommendations to disk
	
	Args:
		d_venues (dict): key is the id of the user, value is a list of the recommended items
		loc (str): Path to save the file
	"""
	dfOut = pd.DataFrame()

	for k, value in d_venue.items():
		df1 = pd.DataFrame(value, columns=["venue_id"])
		df1["user_id"] = k
		dfOut = pd.concat([dfOut, df1])

	dfOut.to_csv(loc, index = False)

	return None

def recommenMatrix(S, X):
	"""
	Get the recomendation matrix

	Args:
		S (scipy.sparse.csr.csr_matrix): Similarity matrix, size n1 x n, where 
			i) n1 is the number of users we are interested to recommend items
			ii) n is the total number of users in the given universe
		X (scipy.sparse.csr.csr_matrix): User-item matrix, size n x m where
			i) n is the total number of users in the given universe
			ii) m is the total number of items in the given universe
	
	Returns:
		R (scipy.sparse.csr.csr_matrix): Size n1 x m, which predicts the preference of the n1 users we are interested in 
	"""

	# For the normalization factor in the recommendation scroes
	w = 1/S.sum(axis=1)
	w = np.array(w).reshape(-1,).tolist()

	D = sp.diags(w)
	R = D.dot(np.dot(S, X)) 

	
	return R

def jaccard_similarity(list1, list2):
    """
    Computes the jaccard similarity between list1 and list2
    Args:
        list1 (list),
        list2 (list).
    
    Returns:
        float: accard similarity
    """

    s1 = set(list1)
    s2 = set(list2)
    return float(len(s1.intersection(s2)) / len(s1.union(s2)))


def __get_key(val, my_dict):
	for key, value in my_dict.items():
		 if val == value:
			 return key
		
	return None

def getNewVenues(R, Y, k, d, topusers):
	"""
	Get the new venues for all the top users
	
	Args:
		R (scipy.sparse.csr.csr_matrix): The user-recommendation matrix for top k users
		Y (scipy.sparse.csr.csr_matrix): User-item matrix for the top k users
		k (int): Number of items to recommend from matrix R, items already rated by the user will be removed.
		d (dict): Dictionary of row and column mappings for user-item matrix 
		topusers (list): User ids of the top k users, this is how the rows of matrices R and Y are labelled
	
	Returns:
		new_venues (dict): key is the id of the user, value is a list of the recommended items
	"""
	new_venues = {} 

	for i in range(len(topusers)):
		r = R.getrow(i).toarray()[0].ravel()
		ind_r = np.argpartition(r, -k)[-k:]

		y = Y.getrow(i).toarray()[0].ravel()
		ind_y = y.nonzero()[0]	

		places = set(ind_r) - set(ind_y)

		new_venues[topusers[i]]  = [__get_key(x,d["col"]) for x in places]

	return new_venues

def getVenues(config):
	"""
	Get a basket of recommendation for top users
	Using the user-user collaborative filtering method
	
	Args:
	    config (dict): Config file params
	
	Returns:
	    [X, topusers, row_col_map] (scipy.sparse.csr.csr_matrix, list, dict)
	    	1) X is the user-item matrix
	    	2) topusers : ontains the ids of the top users
	    	3) row_col_map: row and column mappings for matrix X
	"""

	# Get the top k users
	db = DB(config["DB_path"], top = config["topUsers"])
	topusers = db.topusers	


	# Get the user-item matrix, with the row column mapping
	[row_col_map, X] = db.getUserItemMatrix()

	# Construct Similarity matrix for top users based on cosine similarity of user-item matrix
	index_top = [row_col_map["row"][x] for x in topusers] # index for the top users
	X_top = X[index_top] # user-item matrix for the top users

	# Compute the cosine similarity matrix
	S = cosine_similarity(X_top, X, dense_output=False)

	# Get the similarity matrix based on social network
	S_social = db.getSocialSimilarityMatrix(row_col_map["row"])

	# Close the DB connection
	db.close()

	# Get the recommendation matrix
	R_cosine = recommenMatrix(S, X)
	R_social = recommenMatrix(S_social, X)


	# Get the recommendations for each user using user similarity method
	new_venues = getNewVenues(R_cosine, X_top, config["numberRecommendation"], row_col_map, topusers)
	# Format and save to disk
	savedisk(new_venues, config['loc_recom_venues'])

	# Get the recommendations for each user using social network
	new_venues_social = getNewVenues(R_social, X_top, config["numberRecommendation"], row_col_map, topusers)
	# Format and save to disk
	savedisk(new_venues_social, config['loc_recom_social_venues'])

	return [X, topusers, row_col_map]

def getRecomProbability(X, topusers, d, loc):
	"""
	Get the recommendations based on probabilty scores
	Returns Dataframe which is saved to loc, where columns of dataframe are ['user_id', 'venue_id', 'probability'].
	
	Args:
	    X (scipy.sparse.csr.csr_matrix): User-item matrix
	    topusers (list): Contains the ids of the top users
	    d (dict): row and column mappings for matrix X
	    loc (str): Location to save the recommendations based on probability scores
	
	"""
	d_user_item_prob = {}
	
	# Convert boolean
	X[X.nonzero()]= 1
	m = X.shape[1]

	# Get the column sum of each column of X
	c = X.sum(axis=0)
	c = c/m

	for u in topusers:
		user_index = d["row"][u]
		prob_dict = {}

		# for i in range(m): loop thorugh all items 
		for i in range(15):  # loop thorugh sample items; testing only
			x_i = X[:,i]
			ind_xi = x_i.nonzero()[0]

			prob_i = c[0,i]

			items = X[user_index].nonzero()[1]
			prob_x = np.prod(c[0, items])

			cond_prod =1
			for j in items:
				x_j = X[:,j]
				prob_x_i = (x_j[ind_xi].sum() + 1) / (len(ind_xi)+m+1)
				cond_prod = cond_prod *prob_x_i

			recomm_prod = (cond_prod * prob_i) / prob_x

			prob_dict[__get_key(i, d["col"])] = recomm_prod

		d_user_item_prob[u] = prob_dict

	# Save to disk
	df_prob = pd.DataFrame.from_dict(d_user_item_prob).T
	df_prob.reset_index(inplace=True)
	df_prob.rename(columns={"index": "user_id"}, inplace=True)
	df_prob = df_prob.melt(id_vars=["user_id"], var_name= "venue_id", value_name= "probability")
	df_prob.to_csv(loc, index = False)


	return None

def getRecommendation(config):
	"""
	Get the recommendations based on user similarity, social network and Bayes Theorem

	Args:
		config (dict): Config file params
	"""

	# Get a basket of recommendation for top users based on 1) similarity between users, 2) similarity based on social network graph
	[X, topusers, d] = getVenues(config)

	# Predict the probability via Bayes Theorem
	getRecomProbability(X, topusers, d, config['loc_recom_prob'])

	return None


def getClosenessFriends(df_venue, df_friends, loc):
	"""
	Get the closeness of the users and their friends based on jaccard similarity
	
	Args:
	    df_venue (pd.DataFrame): user and their venue visited
	    df_friends (pd.DataFrame): The users and their friends
	    loc (str): Path to save the output
	
	"""

	s = df_venue.groupby(by = 'user_id')['venue_id'].apply(list)
	d_user_venues = dict(s)
	df_friends["venue_first_user"] = df_friends["first_user_id"].apply(lambda x: d_user_venues.get(x, []))
	df_friends["venue_second_user"] = df_friends["second_user_id"].apply(lambda x: d_user_venues.get(x, []))

	df_friends["Distance"] = df_friends.apply(lambda row: jaccard_similarity(row["venue_first_user"], row["venue_second_user"]), axis=1)

	# Format the output
	df_friends.drop(columns=["venue_first_user", "venue_second_user"], inplace=True)
	df_friends.rename(columns={'first_user_id': 'user_id', 'second_user_id': 'friend_id'}, inplace=True)

	df_friends.to_csv(loc, index = False)

	return None

def analyseSocialUsers(config):
	"""
	Analsye the social users
	
	Args:
	    config (dict): Config file params
	
	"""

	db = DB(config["DB_path"], top = config["topUsers"])

	# Get the social users
	socialusers = db.getSocialUsers()

	# Get the checks of the social users
	df_social = db.getcheckinsSocialUsers(socialusers, config["start_date"])
	df_social.to_csv(config["loc_social_checkins"], index = False)

	# Get the friends of the social users
	df_friends = db.getFriends(tuple(socialusers))

	# Get the venue visited by social users and all friends
	all_ids = tuple(set(df_friends["first_user_id"].unique()).union(df_friends["second_user_id"].unique()))
	df_venue  = db.getVenueIds(all_ids)

	# Close the DB connection
	db.close()

	# Compute the similarity between social users and their friends
	getClosenessFriends(df_venue, df_friends, config['loc_social_closeness'])

	return None


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-config', type=str, help='Path to config file', default = "../data/config/config.json")
	args = parser.parse_args()

	# Open the config file
	with open(args.config, "r") as f:
		config = json.load(f)


	getRecommendation(config)
	analyseSocialUsers(config)


