#!/usr/bin/env python
# encoding: utf-8

import re
import sys
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
config = dotenv_values(".env")

client = MongoClient(config["mongodb_conn"])
db = client["northy"]
db_collection = db["data"]

def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

def normalize_text(text):
	# Clean up string
	text = text["text"].replace("\n", " | ")
	text = text.replace("ALERT: ", "")
	text = text.upper() # normalize
	# Fix bug with ("FLAT STOPPED $RUT | RE-ENTRY LONG | IN: 1795 - 10 PT STOP") where "IN:" contains a colon, all other tweets doesn't
	text = text.replace(" IN: ", "IN ")
	return text

def parse_signal(text):
	text = normalize_text(text)

	# Get all symbols in signal
	symbols = re.findall(r'(\$\w*)', text)
	symbols = unique(symbols)

	ACTIONS = []
	element = 0
	for symbol in symbols:
		symbol = symbol[1:]  # $SPX --> SPX
		ACTION_CODE = f"{symbol}"

		# Move to flat
		if "TO FLAT" in text:
			ACTION_CODE += "_FLAT"

		# Closing trades
		if "CLOSED" in text:
			# There are two types of CLOSE events
			#   *  CLOSED by Stop Loss
			#   *  CLOSED by Profit taking (scale out)

			# profit taking
			if "SCALE" in text:
				ACTION_CODE += "_CLOSE_PROFIT"
			else:
				ACTION_CODE += "_CLOSE_STOPLOSS"

		# Re-entry
		if "RE-ENTRY" in text:
			# Find trade direction
			direction = "LONG" if "LONG" in text else "SHORT"
			ACTION_CODE += f"_TRADE_{direction}"

			# Find entry
			try:
				entries = re.findall(r'(?:IN\s)(\d*)', text)
				ACTION_CODE += f"_IN_{entries[element]}"
			except Exception as e:
				# Sometimes parsing fail. We fall back to "UNKNOWN". We can later on decide, 
				# if we want to ignore this and put a market order in or skip the trade.
				ACTION_CODE += f"_IN_UNKNOWN"
		
			# Find stop loss
			# We don't care to parse the SL from the text. Its always the same anyway
			stoploss_settings = {
				"SPX": 10,
				"RUT": 10,
				"NDX": 25,
			}
			ACTION_CODE += f"_SL_{stoploss_settings[symbol]}"

		element += 1

		ACTIONS.append(ACTION_CODE)

	# debugging
	"""
	for a in ACTIONS:
		if "FLAT" in a:
			print(text)
			print(ACTIONS)
			print()
		if "CLOSE" in a:
			print(text)
			print(ACTIONS)
			print()
		if "TRADE" in a:
			print(text)
			print(ACTIONS)
			print()
	"""
		
	return ACTIONS


def backtest(username="NTLiveStream"):
	result = db_collection.aggregate([
		{
			'$match': {
				'username': username,
				'text': {
					'$regex': re.compile(r"alert:", re.IGNORECASE)
				}
			}
		},
		{
			# Sort, oldest first
			'$sort': {
				'created_at': 1
			}
		},
		{
			'$project': {
				'username': 0,
				'_id': 0
			}
		},
		#{ '$limit' : 5 }
	])

	for tweet in result:
		# The following tweet ID is causing parsing errors. Its a one-off, so we just ignore it. No need to solve for the 1% error rates.
		# FLAT STOPPED $SPX | RE-ENTRY SHORT | IN 4211 - 10 PT STOP. | ADJUSTED $NDX STOP TO -25. |  | TAKING THE STOP RISK OVERNIGHT
		# FLAT STOPPED $NDX $SPX STOPPED $RUT  | RE-ENTRY LONG |IN 3752 |IN 11475 - 25 PT STOP |IN 1129 - 10 PT STOP
		if tweet["tid"] in [1557516667357380608, 1572963969991692292]:
			continue
		signal = parse_signal(tweet)
		print(normalize_text(tweet))
		print(signal)
		print()


if __name__ == '__main__':
	backtest()
