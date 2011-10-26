#!/usr/bin/python

import argparse, urllib, sys, os, re, schema
from lxml import etree
from streetsegmentvalidator import streetsegCheck
from semanticvalidator import semanticCheck
from fullrequiredvalidator import fullrequiredCheck
import magic
import rarfile
import tarfile
import gzip
import zipfile
import bz2
import glob

EXTRACT_PATH = "extracted"
BASESCHEMAURL = "http://election-info-standard.googlecode.com/files/vip_spec_v"
VERSIONLIST = ["2.0","2.1","2.2","2.3","3.0"]
SIZELIMIT = 700000000
FEED_DIR = "/home/votinginfoproject/feeds/"
OUTPUT_DIR = os.getcwd() + "/feedlogs"

m = magic.Magic()

xmlparser = etree.XMLParser()
version = "3.0"

def get_parsed_args():

	parser = argparse.ArgumentParser(description='validate xml')

	parser.add_argument('-s', action='store', dest='schema',
            		help='xsd schema to validate against xml document')

	parser.add_argument('-v', action='store', dest='version',
                        help='xsd version used for validation')

	parser.add_argument('-d', action='store', dest='directory',
			help='directory to search files for')
	
	parser.add_argument('-f', action='append', dest='files',
                        default=[], help='files to validate',)

	parser.add_argument('-o', action='store', dest='output',
                        help='output directory',)

	return parser.parse_args()

def find_largest(file_list):
	large_name = ""
	large_size = 0
	for f in file_list:
		size = os.path.getsize(f)
		if size > large_size:
			size = large_size
			large_name = f
	return large_name

def find_best_match(file_list, fname):
	name = get_base_name(fname)
	temp_list = []
	for f in file_list:
		if f.find(name) >=0:
			temp_list.append(f)
	if len(temp_list) == 0:
		return find_largest(file_list)
	elif len(temp_list) == 1:
		return temp_list[0]
	else:
		return find_largest(temp_list)

def get_base_name(fname):
	new = fname
	if new.rfind("/") >= 0:
		new = new[new.rfind("/")+1:]
	if new.find(".") >= 0:
		new = new[:new.find(".")]
	return new	

def extract_file(path, fname):

	ftype = m.from_file(fname)
	path_extract = path + "/" + EXTRACT_PATH

	if ftype.find("gzip") >= 0:
		gz = gzip.GzipFile(fname, 'rb');
		filedata = gz.read()
		if not os.path.exists(path_extract):
			os.makedirs(path_extract)
		w = open(path_extract + "/feed_data","w")
		w.write(filedata)
		if not os.path.isdir(path_extract+"/feed_data") and not is_archived(path_extract+"/feed_data"):
			newname = get_base_name(fname)
			return os.rename(path_extract+"/feed_data", newname + ".xml")
	elif ftype.find("RAR") >= 0:
		rf = rarfile.RarFile(fname)
		rf.extractall(path=path_extract)
	elif ftype.find("POSIX tar") >= 0:
		tar = tarfile.open(fname)
		tar.extractall(path=path_extract)
	elif ftype.find("bzip2") >= 0:
		bz = bz2.BZ2File(fname, 'rb');
		filedata = bz.read()
		if not os.path.exists(path_extract):
			os.makedirs(path_extract)
		w = open(path_extract + "/feed_data","w")
		w.write(filedata)
		if not os.path.isdir(path_extract+"/feed_data") and not is_archived(path_extract+"/feed_data"):
			newname = get_base_name(fname)
			return os.rename(path_extract+"/feed_data", newname + ".xml")
	elif ftype.find("Zip") >= 0:
		zf = zipfile.ZipFile(fname)
		zf.extractall(path=path_extract)
	else:
		return fname

	if fname.find(EXTRACT_PATH + "/") >= 0:
		os.remove(fname)
	flist = []
	for root, dirs, dirfiles in os.walk(path_extract):
		for name in dirfiles:
			flist.append(root + "/" + name)
	print str(flist)
	if len(flist) > 1:
		fname = extract_file(path, find_best_match(flist, fname))
	else:
		fname = extract_file(path, flist[0])
	return fname

def is_archived(fname):
	ftype = m.from_file(fname)
	if ftype.lower().find("zip") or ftype.find("POSIX tar") or ftype.find("RAR"):
		return True
	return False 

results = get_parsed_args()

if results.version:
	version = results.version
if version == "2.2":
	fschema = urllib.urlopen(BASESCHEMAURL + version + "a.xsd")
else:
	fschema = urllib.urlopen(BASESCHEMAURL + version + ".xsd")

schema = schema.Schema(fschema)

files = []

if results.directory or len(results.files) <= 0:
	if results.directory:
		directory = results.directory
	else:
		directory = FEED_DIR

	for root, dirs, dirfiles in os.walk(directory):
		for name in dirfiles:
			path = root + "/" + name
			print path
			if path.find("/.") > 0 or path.endswith("~") or path.find("/extracted/") > 0:
				continue
			elif path.endswith(".xml"):
				files.append(path)
			elif is_archived(path):
				extracted = extract_file(root, path) 
				if extracted.endswith(".xml"):
					files.append(extracted)
			print files
						
if len(results.files) > 0:
        fnames = results.files
        for f in fnames:
                files.append(f)

if results.output:
	outputdir = results.output
else:
	outputdir = OUTPUT_DIR
if not os.path.exists(outputdir):
	os.makedirs(outputdir)

for fname in files:
	basename = get_base_name(fname)
	fulldir = outputdir + "/" + basename + "logs"

	if not os.path.exists(fulldir):
		os.makedirs(fulldir)

	#pass output dir to everything
	#zip at end
	#remove extracted files and directories, requires another cycle through the files at the end
	print fname        
	data = etree.parse(open(fname),xmlparser)
        root = data.getroot()

        filesize = os.path.getsize(fname)
        if filesize < SIZELIMIT:
                basicCheck = schema.xmlschema.validate(data)
                print "Basic Schema Check for " + str(fname) + ": " + str(basicCheck)
        else:
                basicCheck = False

        semanticCheck(root, schema, basename, fulldir)

        if filesize < SIZELIMIT:
                streetsegCheck(fname, basename, fulldir)
		if not(basicCheck):
	                data = etree.parse(open(fname), xmlparser)
        	        root = data.getroot()
        else:
                print "File too large to run street segment check on"

        if not(basicCheck):
                fullrequiredCheck(root, schema, basename, fulldir)
