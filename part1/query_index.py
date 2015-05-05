from __future__ import division
import argparse
import sys
import json
import re
import porter_stemmer
import math
import operator

def tf_idf(word_dlist, bs_id, tot_n_rev):	
	f_td = 0
	n_rev = 0
	revs = set()
	for r_dict in word_dlist:
		cur_rev_id = r_dict["review_id"]
		if r_dict["business_id"] == bs_id: # considers all reviews for specific business as one single review for tf FIXME
			f_td += 1
		if cur_rev_id not in revs:
			revs.add(cur_rev_id)
			n_rev += 1

	tf = 1 # logarithmically scaled frequency
	if f_td != 0:
		tf += math.log(f_td)

	idf = math.log(1 + (tot_n_rev / n_rev))
	return tf*idf 

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-indexFile', required = True, help = 'path to inverted index file')
	parser.add_argument('-businessFile', required = True, help = 'path to business json file')
	parser.add_argument('-stopWord', help = 'path to newline separated stopword list file. Default is None.\n BE SURE TO USE SAME STOPWORD FILE AS IN create_index.py')
	parser.add_argument('-revNum', required = True, help = 'total number of reviews. You`ll have to get this by running create_index.py first')
	opts = parser.parse_args()
	index_dict = {}	
	print "Reading in inverse index file..."	

	with open(opts.indexFile, 'r') as index_file:
		for line in index_file:
			data = json.loads(line)
			index_dict[data[0]] = data[1:]	

	bs_dict = {}
	print "Reading in business file..."
	with open(opts.businessFile, 'r') as business_file:
		for line in business_file:
			data = json.loads(line)
			bs_dict[data["business_id"].encode('utf-8')] = (data["city"].encode('utf-8').lower(), data["review_count"], data["stars"], data["name"].encode('utf-8'))


	stpWord = set()
	if opts.stopWord is not None:
		print "Reading stopword file..."
		with open(opts.stopWord, 'r') as stpWord_file:
			for line in stpWord_file:
				stpWord.add(line.strip())

	stemmer = porter_stemmer.PorterStemmer()
	print "Done. Waiting for input"
	# Start getting input from stdin
	while 1:
		usr_input = sys.stdin.readline()
		if not usr_input:
			break
		input_list = usr_input.strip().split("IN", 1)
		#print input_list	

		raw_words = input_list[0].rstrip().lower()
		is_PQ = 0	

		if raw_words[0] == '\"':
			raw_words = raw_words.strip('\"')
			is_PQ = 1

		is_LSQ = 0
		if len(input_list) == 2:
			is_LSQ = 1

		raw_word_list = raw_words.split() # apply same tokenization
		word_list = [stemmer.stem(word, 0, len(word) - 1) for word in raw_word_list if word not in stpWord]

		if len(word_list) == 0:
			print "There has to be at least one non-stopword word"
			continue

		if len(word_list) == 1 and is_PQ == 1:
			print "There has to be at least two non-stopword words to process PQ"
			continue	

		loc_list = None
		
		if is_LSQ:
			loc_list = input_list[1].lower().split()
			if not len(loc_list):
				print "There has to be at least one city for LSQ"
				continue

		f_list = None # indicator variable

		if not is_PQ: 
			final_list = []
			for word in word_list:
				wb = set()
				if word not in index_dict:
					final_list = None
					break
				for r_dict in index_dict[word]:	
					if not is_LSQ:
						wb.add(r_dict["business_id"])
					else:
						if bs_dict[r_dict["business_id"]][0] in loc_list:
							wb.add(r_dict["business_id"])
				final_list.append(wb)

			if final_list == None:
				print " "
				continue
			f_list = list(set.intersection(*final_list))
		else:
			it = 1
			wb = {}	
			for word in word_list:	
				if word not in index_dict:
					wb = None
					break
				if it == 1: # First iteration	
					for r_dict in index_dict[word]:
						if not is_LSQ:
							wb[r_dict["business_id"]] = (r_dict["review_id"], r_dict["position"])	
						else:
							if bs_dict[r_dict["business_id"]][0] in loc_list:
								wb[r_dict["business_id"]] = (r_dict["review_id"], r_dict["position"])
				else: # >= 2nd iteration
					bs_set = set() # another set to keep track of this iteration
					for r_dict in index_dict[word]:	
						bs_id = r_dict["business_id"]
						if bs_id in wb:
							if wb[bs_id][0] == r_dict["review_id"]:
								if (wb[bs_id][1] + 1) == r_dict["position"]:
									bs_set.add(bs_id)
									wb[bs_id] = (r_dict["review_id"], r_dict["position"])
					for bid in (set(wb.keys()) - bs_set): # remove invalid bids
						wb.pop(bid)
				it += 1		
		
			if wb == None:
				print" "
				continue
			f_list = [key for key in wb]	

		fin_dict = {}
		if len(f_list) == 0:
			print " "
			continue
		for bs in f_list:
			score = 0
			for word in word_list:
				score += tf_idf(index_dict[word], bs, int(opts.revNum))
			score = score * math.log(bs_dict[bs][1]) * bs_dict[bs][2]
			fin_dict[bs_dict[bs][3]] = score

		ret = sorted(fin_dict.items(), key = operator.itemgetter(1), reverse=True)	
		n = max(len(ret), 10)
		print ret[:n]

if __name__ == '__main__':
	main()
