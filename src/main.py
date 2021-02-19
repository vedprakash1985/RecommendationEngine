# -*- coding: utf-8 -*-
# @Author: Ved Prakash
# @Date:   2021-02-18 10:48:30
# @Last Modified by:   Ved Prakash
# @Last Modified time: 2021-02-19 12:41:22

# Main Script to run for Questions 1 ans 2 in Outline

import pandas as pd 
import argparse
import json
# Import from local modules
from DB import DB


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

	# Construct Similarity matrix for top users


	# Close the DB connection
	db.close()



	return None

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
