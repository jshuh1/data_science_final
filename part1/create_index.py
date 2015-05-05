import json
import argparse
import porter_stemmer
import re

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-reviewFile', required=True, help='Path to review data')
	parser.add_argument('-stopWord', help='Path to newline separated stopword list file. Default is None')
	parser.add_argument('-outputName', help='output file name. Default is output.json')
	opts = parser.parse_args()

	stpWord = set()
	if opts.stopWord is not None: # add words in stopword file to default list
		for line in open(opts.stopword, 'r'):
			stpWord.add(line.strip())

	inv_index = {}
	stemmer = porter_stemmer.PorterStemmer()	

	line_num = 1
	for line in open(opts.reviewFile, 'r'):
		obj = json.loads(line)
		text = obj["text"].encode('utf-8').lower()
		text = re.sub(r'\W+', ' ', text)
		bus_id = obj["business_id"].encode('utf-8')
		rev_id = obj["review_id"].encode('utf-8')
		position = 1
		for word in text.split():
			if word in stpWord:
				continue
			word = stemmer.stem(word, 0, len(word) - 1)
			data_structure = {"business_id": bus_id, "review_id": rev_id, "position": position}
			if word not in inv_index:
				inv_index[word] = [data_structure]
			else:
				inv_index[word].append(data_structure)
			position += 1
		line_num += 1

	print "Total review count: " + str(line_num)
	print "You'll need this number for query_index.py"

	outName = 'output.json'
	if opts.outputName is not None:
		outName = opts.outputName
	
	with open(outName, 'w') as fp:	
		for word in inv_index:
			json.dump([word] + inv_index[word], fp)
			fp.write('\n')

	# TODO works fine. However, fix trivial cases such as number or single word

if __name__ == '__main__':
	main()
