"""
WordEmbeddingPlatform
Copyright 2017 Northwestern University

This is a word embedding selection , query and download platform of which function is to
facilitate natural language processing researcher to use word embeddings more efficiently.

Associated with this platform is a broker-centered model. You might want to check the details
at http://40i123952-4-24305=234052o=2.com

"""

import re
from os import path

from setuptools import setup, find_packages


def read(*paths):
	filename = path.join(path.abspath(path.dirname(__file__)),*paths)
	with open(filename) as f:
		return f.read()


setup(
	name = 'WordEmbeddingPlatform',
	description = 'Python library for word embeddings',
	long_description = read('README.md'),
	url = 'https://github.com/MarcusYYY/WordEmbeddingPlatform',
	author = 'Marcus',
	author_email = 'marcusyuzc1992@gmail.com',
	license = 'Apache 2.0',
	packages = find_packages(),
	keywords = [
		'WordEmbeddingPlatform',
		'EP'
	],
	classifiers = [
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'Intended Audience :: Science/Research',
		'Operating System :: OS Independent',
		'License :: OSI Approved :: Apache Software License',
		'Programming language :: Python :: 2',
		'Programming language :: Python :: 2.7',
		'Programming language :: Python :: 3',
		'Programming language :: Python :: 3.4',
		'Programming language :: Python :: 3.5',
		'Programming language :: Python :: 3.6',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Topic :: Scientific/Engineering :: Information Analysis',
	],

	install_requires=[
		'pandas',
		'numpy',
		'urllib',
		'urllib2',
		'requests',
		'sys',
		'os',
		'zipfile',
		'gensim',
		'string',
		'collection',
		're',
		'nltk',
		'codecs',
		'scipy',
		'gensim',
		'datadotworld',
		'collection',
		'pprint',
		'cPickle',
		'operator',
	],

	)