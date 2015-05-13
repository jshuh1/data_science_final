from __future__ import division
import json
import argparse
import porter_stemmer
import re
import sys
import time 

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-reviewFile', required=True, help='Path to review data')
	parser.add_argument('-stopWord', help='Path to newline separated stopword list file. Default is None')	
	opts = parser.parse_args()

	tot_line = 1550000
	blk = 100000 # hard coded bulk for time calculation

	stpWord = set()
	if opts.stopWord is not None: # add words in stopword file to default list
		for line in open(opts.stopWord, 'r'):
			stpWord.add(line.strip())

	inv_index = {}
	stemmer = porter_stemmer.PorterStemmer()	

	start_time = time.clock()

	linenum = 1	
	for line in open(opts.reviewFile, 'r'):
		obj = json.loads(line)
		text = obj["text"].encode('utf-8').lower()
		text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
		bus_id = obj["business_id"].encode('utf-8')	
		position = 1
		for word in text.split():
			if word in stpWord or len(word) == 1:
				continue # skip stopword or word of length 1
			word = stemmer.stem(word, 0, len(word) - 1)
			data_structure = ( bus_id, linenum, position)
			if word not in inv_index:
				inv_index[word] = [data_structure]
			else:
				inv_index[word].append(data_structure)
			position += 1		
	
		if linenum % blk == 0:
			end_time = time.clock()
			elapsed = end_time - start_time
			rm_estimate = (tot_line/linenum - 1)*elapsed
			sys.stderr.write("Line " + str(linenum) + " reached\n")
			sys.stderr.write("Time elapsed: " + str(elapsed)+"\n")
			sys.stderr.write("Estimated time remaining: " + str(rm_estimate) + "\n")
		linenum += 1

	sys.stderr.write("Done. Writing inverted index to stdout\n")	
	
	#Line-by-line dumping for the ease of debugging
	for word in inv_index:
		json.dump([word] + inv_index[word], sys.stdout)
		print "" 

	
if __name__ == '__main__':
	main()
