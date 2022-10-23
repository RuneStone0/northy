#!/usr/bin/env python
# encoding: utf-8

import re
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
config = dotenv_values(".env")

client = MongoClient(config["mongodb_conn"])
db = client["northy"]
db_collection = db["data2"]

result = client['northy']['data2'].aggregate([
	{
		'$match': {
			'account_name': {
				'$eq': 'NTLiveStream'
			}
		}
	}, {
		'$match': {
			'text': {
				'$regex': re.compile(r"alert", re.IGNORECASE)
			}
		}
	}, 
	{
		'$project': {
			'account_name': 0,
			'_id': 0
		}
	}
])

actions = {
	"ADJUST_FLAT",  # Change stop loss to break even (flat)
	"STOP_OUT",  # Position was automatically stopped out
}


def ADJUST_FLAT():
	print("ADJUST_FLAT")
	return "ADJUST_FLAT"


for t in result:
	text = t["text"].replace("\n", " | ")
	id = t["tid"]
	out = f"{id} {text}"
	#if "flat" in text:
	#	print(out)

	a = ['a', 'b', 'c']
	matches = ["stop adjusted to flat"]

	if text.count("$") > 1:
		print(out)

	#if any(x in text for x in matches):
	#	out = "ADJUST_FLAT " + out

		#print(out)
	
