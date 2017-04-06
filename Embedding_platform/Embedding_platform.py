import pandas as pd
import numpy as np
import urllib,urllib2,requests,numpy,sys,os,zipfile,gensim,string,collections,re,nltk,requests,codecs
from scipy import spatial
from gensim.models import Word2Vec
from nltk.tokenize import sent_tokenize,word_tokenize
import datadotworld as dw
from collections import Counter
from pprint import pprint
import cPickle as pickle
from operator import itemgetter

hdv_vocab = []

def report(count, blockSize, totalSize):
	percent = float(count*blockSize*100/totalSize)
	sys.stdout.write("\r%d%%" % percent + ' complete')
	sys.stdout.flush()

# SQL query for specific word embedding in given table
def query_embeddings(table,word):
	embedding_list = pd.read_csv('https://query.data.world/s/4o7h67xz3m3zgsui7tk08yst8')
	table_list = embedding_list['table']
	format_list = embedding_list['file_format']
	if format_list[table_list == table].values[0] != 'csv':
		print 'Sorry for the inconvenience but we are not able to query Non-csv file.'
		return 
	dataset_ = "marcusyyy/northwestern-word-embedding"
	query_ = 'SELECT * FROM ' + table + " where `Column A` = '" + word + "'"
	try:
		results = dw.query(dataset_, query_)
		ans = []
		ans.append(word)
		num = results.dataframe.values[0][1:]
		ans.extend(num)
		print ans
		return ans
	except RuntimeError,e:
		print e

# Get the subset of the pretrained embeddings according to the raw text input.
def EmbedExtract(file_dir,table,batch = 200,pad = False,check = False):
	texts = ''
	for name in sorted(os.listdir(file_dir)):
		path = os.path.join(file_dir, name)
		if os.path.isdir(path):
			for fname in sorted(os.listdir(path)):
				fpath = os.path.join(path, fname)
				if sys.version_info < (3,):
					f = open(fpath)
				else:
					f = open(fpath, encoding='latin-1')
				texts = texts + f.read()
	input_txt = []
	sentences = sent_tokenize(texts)
	for s in sentences:
		tokens = word_tokenize(s)
		input_txt = input_txt + tokens
	inp_vocab = set(input_txt)
	inp_vsize = (len(inp_vocab))

	dataset_ = "marcusyyy/northwestern-word-embedding"
	query_ = ''
	final_result = []
	back_query = ''
	print 'Embedding extraction begins.'
	words = list(inp_vocab)
	i = 0
	back_up_i = 0
	while i < len(words):
		if i > 500:
			break
		if i == 0:
			query_ = 'SELECT * FROM ' + table + " where `Column A` = '" + words[i] + "'"
		elif i % batch == 0:
			process = str((i)*100/len(words))
			try:
				results = dw.query(dataset_, query_)
				print process + "%" + ' has been completed.'
				back_query = query_
				back_up_i = i
			except RuntimeError,e:
				i = back_up_i
				print 'Batch size ' + str(batch)
				batch = int(batch * 0.9)
				if batch == 0:
					print "404 Error"
					break
				print 'Batch size too large. Reducing to ' + str(batch)
				continue
			vector = results.dataframe.values
			final_result.extend(vector)
			query_ = 'SELECT * FROM ' + table + " where `Column A` = '" + words[i] + "'"
		else:
			query_ = query_ + " OR `Column A` = '" + words[i] + "'"
		i = i + 1
	print 'Embedding successfully extracted.'
	word_vector = {}
	ans = ''
	if pad == True:
		for word in inp_vocab:
			if not word_vector.has_key(word):
				subset = []
				subset.append(word.encode('utf-8'))
				zero = np.zeros(final_result[0].shape[0]-1)
				subset.extend(zero)
				subset = np.asarray(subset,dtype=object)
				final_result.append(subset)

	for vector in final_result:
		word = str(vector[0])
		embed = np.array2string(vector[1:])[1:-1]
		embed = embed.replace('\n','')
		word_vector[word] = embed
		ans = ans + word + ' ' + embed + '\n'
	overlap_words = []
	for word in word_vector:
		overlap_words.append(word)
	int_count = int(len(set.intersection(set(overlap_words),set(words))))
	missing_words = str(len(words) - int_count)
	percent = str(int_count * 100 / len(words))
	print 'There are ' + missing_words + " tokens that can't be found in this pretrained word embedding."
	print percent + "%" + " words can be found in this pretrained word embedding."
	if check:
		print ans
	return final_result


def HighDensityVocab(tolerance = 0.85,num = 5000,num_stopwords = 200):
	embedding_list = pd.read_csv('https://query.data.world/s/4o7h67xz3m3zgsui7tk08yst8')
	print 'Infomation of the current avaliable embeddings.'
	print embedding_list
	print str(num_stopwords) + ' most frequent words will be removed as stop words.'
	print "Pick up " + str(num) + ' top frequent words as signature of all avaliable embeddings.'
	url_list = embedding_list['url']
	name_list = embedding_list['embedding_name']
	format_list = embedding_list['file_format']
	files = []
	threshold = int(0.5 + tolerance * len(url_list))	
	emb_vocab = {}

	#fetch the embedding from data.world and output the high density vocab for each existing embedding
	for idx,url in enumerate(url_list):
		print 'Fetching '+ name_list.iloc[idx] +' embeddings and creating its signature.'
		if format_list[idx] != 'csv':
			print "Can't fetch embedding because incorrect file format."
			continue
		file = pd.read_csv(url,header = None,error_bad_lines=False)
		wordlist = file.iloc[0:num_stopwords][0].values
		files.append(file)
		for word in wordlist:
			if ( word not in emb_vocab):
				emb_vocab.update({word: 1})
			else:
				emb_vocab[word] += 1
	print 'Processing High Density Vocabulary list.'
	for key in emb_vocab:
		if (emb_vocab[key] >= threshold):
			hdv_vocab.append(key)
	print "High Density Vocabulary found in at least ",tolerance *100, " percent of embeddings."
	
	#Create a dictionary of which keys are embedding names and values are lists of high freq words(signature)
	signature = {}
	for index,file in enumerate(files):
		hf_words = file.iloc[0:num][0].values
		sig_vocab = []
		for word in hf_words:
			if word not in hdv_vocab:
				sig_vocab.append(word)
		signature[name_list.iloc[index]] = sig_vocab
	return signature,hdv_vocab

#Input is the raw txt file, and output is the 5000 top frequent words(signature) of this raw corpus
def RankVocabGenerator(inp_dir,num = 5000):

	cnt = Counter()
	# Counter for all words in the corpus
	try:
		for (root, dirs, files) in os.walk(inp_dir):

			files = [f for f in files if not f[0] == '.']
			for f in files:
				filepath = os.path.join(root,f)

				# CHANGE: Update Codec as needed for test corpus
				with codecs.open(filepath,'rb', encoding="cp1252") as f:
					decoded_txt = f.read()
					tok_txt = word_tokenize(decoded_txt.lower())
					for word in tok_txt:
						for ch in word:
							if (ch not in string.punctuation and ch not in string.digits):
								cnt[word] += 1
								break
		print "Pick top " + str(num) + " most frequently occurring words in the corpus as signature. "
	except:
		print "No such file or your directory of corpus can't be found."
		return
    # Delete HDF Words
    # Update with correct high density vocab filename
	for word in hdv_vocab:
		if word in cnt.keys(): del cnt[word]

	corpus_name = inp_dir.split('/')[-1]
    # Pickle dump an ordered list of 5000 most common words
	vocab = [str(word[0]) for word in  cnt.most_common(num)]
	return vocab

def method_a(inp_dir,num_sig,num_sig_embedding,num_stopwords):

	rank_dict = dict()
	signature,hf_vocab = HighDensityVocab(num = num_sig_embedding,num_stopwords = num_stopwords)
	test_vocab = RankVocabGenerator(inp_dir,num_sig)

	for embed in signature:
		rank_dict.update({embed: 0})
		for ind in range(0,len(signature[embed])):
			curr_inpword = signature[embed][ind]
			if curr_inpword in test_vocab:
				rank_dict[embed] += test_vocab.index(curr_inpword)/float(len(test_vocab))
			else:
				rank_dict[embed] += len(signature[embed])/float(len(test_vocab))
	print "The following list is the score of each embedding get in method A.They are sorted in descending order."
	pprint (sorted(rank_dict.items(),key=itemgetter(1)))
    # return key in rank_dict such that value is lowest

def check():
	embedding_list = pd.read_csv('https://query.data.world/s/4o7h67xz3m3zgsui7tk08yst8')
	print 'Embeddings now avaliable.'
	print embedding_list

class embedding: 
	# Initiate the embedding class and check if the embedding we want exists
	def __init__(self,name=None,dimension=None,path='_'):
		# Load the whole list of current availiable embeddings
		embedding_list = pd.read_csv('https://query.data.world/s/4o7h67xz3m3zgsui7tk08yst8')
		embedding_names = embedding_list['embedding_name']
		embedding_sizes = embedding_list['vocabulary size']
		embedding_dimensions = embedding_list['dimension']
		embedding_score = 0
		if name == None:
			if len(embedding_list):
				print 'Embeddings now avaliable.'
				print embedding_list
			else:
				print "No embedding is avaliable now."

		self.name = name
		self.dimension = dimension
		self.flag = True

		if name in embedding_names.values:
			url = embedding_list[embedding_names == name]['url'].values[0]
			print 'The embedding you are looking for exists. The url is',url
			self.url = url

			if embedding_list[embedding_names == name]['dimension'].values[0] != dimension:
				print "But the dimension you asked for does not exist."
				self.flag = False

			elif type(embedding_list[embedding_names == name]['dimension'].values[0]) == str:
				if len(embedding_list[embedding_names == name]['dimension'].values[0].split('_')) == 1:
					if embedding_list[embedding_names == name]['dimension'].values[0].split('_')[0] != str(dimension):
						print "But the dimension you asked for does not exist."
						self.flag = False
				else:
					dimension_pool = embedding_list[embedding_names == name]['dimension'].values[0].split('_')
					if str(dimension) not in dimension_pool:
						print "But the dimension you asked for does not exist."
						self.flag = False

		else:
			print 'The embedding you are looking for does not exist.'
			self.flag = False
		
		if self.flag:
			try:
				self.size = int(embedding_list[embedding_names == name]['vocabulary size'].values[0])
			except:
				if embedding_list[embedding_names == name]['vocabulary size'].values[0][-1] == 'K':
					num = embedding_list[embedding_names == name]['vocabulary size'].values[0][:-1]
					num = int(num) * 1000
					embedding_list[embedding_names == name]['vocabulary size'].values[0] = num
				else:
					num = embedding_list[embedding_names == name]['vocabulary size'].values[0][:-1]
					num = int(num) * 1000000
					embedding_list[embedding_names == name]['vocabulary size'].values[0] = num
			self.path = path
			self.dl = False
			self.destination = None
			self.vector = None
			self.embed = None
			self.table = embedding_list['table'][embedding_names == name]

	# Download the embeddings in the broker file on data.world and save them 
	# on the local files.
	def download(self,file_format = 'csv'):
		if self.flag:
			url = self.url
			path = self.path
			if file_format == 'zip':
				name = url.split('/')[-1]
				if not os.path.exists(path) and path != '_':
					os.makedirs(path)
				urllib.urlretrieve(url,path + name,reporthook = report)
				self.destination = path + name
				print self.destination
				print 'The embedding path is %s .' % os.path.join(os.getcwd(),self.destination)
			else:
				if file_format == 'txt':
					if not os.path.exists(path) and path != '_':
						os.makedirs(path)
					r = requests.get(url,stream = True)
					self.destination = path + self.name + '.txt'
					with open(self.destination,'wb') as f:
						for chunk in r.iter_content(chunk_size = 1024):
							if chunk:
								f.write(chunk)
					print 'The embedding path is %s .' % os.path.join(os.getcwd(),self.destination)
				elif file_format == 'csv':
					if not os.path.exists(path) and path != '_':
						os.makedirs(path)
					self.destination = path + self.name + '.csv'
					df = pd.read_csv(self.url)
					df.to_csv(self.destination,index = False)
					print 'The embedding path is %s .' % os.path.join(os.getcwd(),self.destination)
			self.dl = True
		else:
			print "You can't download the embedding because errors happened."
			self.dl = False
		embed = None
		#Extract embedding from zip file or txt file.
		if self.dl:
			if zipfile.is_zipfile(self.destination):
				zf = zipfile.ZipFile(self.destination,'r')
				names = zf.namelist()
				if len(names) != 1:
					dimension = self.dimension
					for filename in names:
						try:
							data = zf.read(filename)
							dimension_of_embed = data.split('\n')[1].split(' ')
							if len(dimension_of_embed) == dimension + 1:
								embed = data
						except KeyError:
							print 'ERROR: Did not find %s in zip file' % filename
				else:
					embed = zf.read(names[0])
			else:
				file = open(self.destination)
				embed = file.read()
			self.embed = embed
			#store the word vector into dictionary
			word_vector = {}
			cach = embed.split('\n')
			for num,row in enumerate(cach):
				if file_format == 'csv':
					values = row.split(',')
				else:
					values = row.split()
				if len(values) < 3:
					continue
				try:
					word = values[0]
					coefs = numpy.asarray(values[1:],dtype = 'float32')
					word_vector[word] = coefs
				except:
					continue
			self.vector = word_vector
			print 'Word embedding has been successfully downloaded.'
			print 'Check the vector attribute by using embedding_name.vector.'
			return word_vector
		else:
			print "The embedding you asked can't be downloaded."
