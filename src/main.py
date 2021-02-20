# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 10:48:30
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-21 07:42:03

# Main Script to run for Questions 1 ans 2 in Outline

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

def getRecomProbability(X, topusers, d):
	"""
	Get the recommendations based on probabilty scores
	Args:
		X (scipy.sparse.csr.csr_matrix): User-item matrix
		topusers (list): Contains the ids of the top users
		d (dict): row and column mappings for matrix X
	
	Returns:
		d_user_item_prob (dict): TODO
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

		for i in range(m):  # loop thorugh all items 
			x_i = X[:,i]
			ind_xi = x_i.nonzero()[0]

			prob_i = c[0,i]

			items = X[user_index].nonzero()[1]
			prob_x = np.prod(c[0, items])

			cond_prod =1
			for j in items:
				x_j = X[:,j]
				prob_x_i = (x_j[ind_xi].sum() + 1) / len(ind_xi)
				cond_prod = cond_prod *prob_x_i

			recomm_prod = (cond_prod * prob_i) / prob_x

			prob_dict[__get_key(i, d["col"])] = recomm_prod

		d_user_item_prob[u] = prob_dict


	return d_user_item_prob 

def getRecommendation(config):
	"""
	Get the recommendations based on user similarity, social network and Bayes Theorem
	Args:
		config (dict): Config file params
	"""

	# Get a basket of recommendation for top users based on 1) similarity between users, 2) similarity based on social network graph
	[X, topusers, d] = getVenues(config)

	# Predict the probability via Bayes Theorem
	out_d = getRecomProbability(X, topusers, d)

	# TODO: Testing: Broke here for one of the terminal

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


	# Close the DB connection
	db.close()

	return None


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-config', type=str, help='Path to config file', default = "../data/config/config.json")
	args = parser.parse_args()

	# Open the config file
	with open(args.config, "r") as f:
		config = json.load(f)


	# getRecommendation(config)
	analyseSocialUsers(config)


