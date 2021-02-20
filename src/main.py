# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 10:48:30
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-20 10:12:50

# Main Script to run for Questions 1 ans 2 in Outline

import pandas as pd 
import argparse
import json
import numpy as np
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity

# Import from local modules
from DB import DB


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


def getVenues(config):
	"""
	Get a basket of recommendation for top users
	Using the user-user collaborative filtering method
	Args:
		config (dict): Config file params
	
	Returns:
		TYPE: Description
	"""

	# Get the top k users
	db = DB(config["DB_path"], top = config["topUsers"])
	topusers = db.getTopUsers()

	# Get the user-item matrix, with the row column mapping
	[row_col_map, X] = db.getUserItemMatrix()

	# Close the DB connection
	db.close()

	# Construct Similarity matrix for top users based on cosine similarity of user-item matrix
	index_top = [row_col_map["row"][x] for x in topusers] # index for the top users
	X_top = X[index_top] # user-item matrix for the top users

	# Compute the cosine similarity matrix
	S = cosine_similarity(X_top, X, dense_output=False)

	# Get the recommendation matrix
	R_cosine = recommenMatrix(S, X)


	# Get the recommendation for each user
	df_venues = getNewVenues(R_cosine, X_top)

	return df_venues

def getRecommendation(config):
	"""Summary
	
	Args:
		config (dict): Config file params
	
	Returns:
		TYPE: Description
	"""

	# Get a basket of recommendation for top users
	df_venues= getVenues(config)

	return None




if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('-config', type=str, help='Path to config file', default = "../data/config/config.json")
	args = parser.parse_args()

	# Open the config file
	with open(args.config, "r") as f:
		config = json.load(f)


	getRecommendation(config)
