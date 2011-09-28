#!/usr/bin/python

import argparse, urllib, sys, os, re, schema
from lxml import etree
from streetsegmentvalidator import streetsegCheck
from semanticvalidator import semanticCheck
from fullrequiredvalidator import fullrequiredCheck

def get_parsed_args():

	parser = argparse.ArgumentParser(description='validate xml')

	parser.add_argument('-s', action='store', dest='schema',
            		help='xsd schema to validate against xml document')

	parser.add_argument('-v', action='store', dest='version',
                        help='xsd version used for validation')

	parser.add_argument('-f', action='append', dest='files',
                        default=[], help='files to validate',)

	return parser.parse_args()

BASESCHEMAURL = "http://election-info-standard.googlecode.com/files/vip_spec_v"
VERSIONLIST = ["2.0","2.1","2.2","2.3","3.0"]
SIZELIMIT = 500000000
FEED_DIR = "/home/jensen/vip/archiver/"

xmlparser = etree.XMLParser()
version = "2.3"

results = get_parsed_args()

if results.version:
	version = results.version

if version == "2.2":
	fschema = urllib.urlopen(BASESCHEMAURL + version + "a.xsd")
else:
	fschema = urllib.urlopen(BASESCHEMAURL + version + ".xsd")

schema = schema.Schema(fschema)

if len(results.files) <= 0:
	
	dirlist = os.listdir(FEED_DIR)

	for folders in dirlist:
		if os.path.isdir(FEED_DIR + folders):
			files = os.listdir(FEED_DIR + folders)
			for f in files:
				fname = FEED_DIR + folders + "/" + f
				if os.path.isfile(fname) and fname.endswith(".xml"):
					data = etree.parse(open(fname),xmlparser)
					root = data.getroot()

					filesize = os.path.getsize(fname)
					if filesize < SIZELIMIT:
						basicCheck = schema.xmlschema.validate(data)
						print "Basic Schema Check for " + str(f) + ": " + str(basicCheck)
					else:
						basicCheck = False
					
					semanticCheck(root, schema, fname)
					
					if filesize < SIZELIMIT:
						streetsegCheck(fname)
						data = etree.parse(open(fname), xmlparser)
						root = data.getroot()
					else:
						print "File too large to run street segment check on"
					
					if not(basicCheck):
						fullrequiredCheck(root, schema, fname)
else:
	files = results.files[0]
	for fname in files:
		data = etree.parse(open(fname),xmlparser)
		root = data.getroot()

		filesize = os.path.getsize(fname)
		if filesize < SIZELIMIT:
			basicCheck = schema.xmlschema.validate(data)
			print "Basic Schema Check for " + str(f) + ": " + str(basicCheck)
		else:
			basicCheck = False
					
		semanticCheck(root, schema, fname)
					
		if filesize < SIZELIMIT:
			streetsegCheck(fname)
			data = etree.parse(open(fname), xmlparser)
			root = data.getroot()
		else:
			print "File too large to run street segment check on"
					
		if not(basicCheck):
			fullrequiredCheck(root, schema, fname)

