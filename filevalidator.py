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
SIZELIMIT = 500000000
FEED_DIR = "/home/votinginfoproject/feeds/"

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

def check_file(path, fname):
	ftype = m.from_file(fname)
	if ftype.find("gzip") >= 0:
		gz = gzip.GzipFile(fname, 'rb');
		filedata = gz.read()
		if not os.path.exists(path + "/" + EXTRACT_PATH):
			os.makedirs(path + "/" + EXTRACT_PATH)
		w = open(path + "/" + EXTRACT_PATH + "/feed_data","w")
		w.write(filedata)
	elif ftype.find("RAR") >= 0:
		rf = rarfile.RarFile(fname)
		rf.extractall(path=path+"/"+EXTRACT_PATH)
	elif ftype.find("POSIX tar") >= 0:
		tar = tarfile.open(fname)
		tar.extractall(path=path+"/"+EXTRACT_PATH)
	elif ftype.find("bzip2") >= 0:
		bz = bz2.BZ2File(fname, 'rb');
		filedata = bz.read()
		if not os.path.exists(path + "/" + EXTRACT_PATH):
			os.makedirs(path + "/" + EXTRACT_PATH)
		w = open(path + "/" + EXTRACT_PATH + "/feed_data","w")
		w.write(filedata)
	elif ftype.find("Zip") >= 0:
		zf = zipfile.ZipFile(fname)
		zf.extractall(path=path+"/"+EXTRACT_PATH)
	else:
		return fname
	if fname.find("extracted/") >= 0:
		os.remove(fname)
	flist = glob.glob(path + "/" + EXTRACT_PATH + "/*")
	if len(flist) > 1:
		check_file(find_largest(flist))
	else:
		check_file(flist[0])

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

        dirlist = os.listdir(directory)
        for folders in dirlist:
                if os.path.isfile(directory + folders) and folders.endswith(".xml"):
                        files.append(directory + folders)
		elif os.path.isfile(directory + folders):
			decompressed = check_file(directory, folders)
			if decompressed.endswith(".xml"):
				files.append(decompressed)
                elif os.path.isdir(directory + folders):
                        fnames = os.listdir(directory + folders)
                        for fname in fnames:
                                path = directory + folders + "/" + fname
                                if os.path.isfile(path) and path.endswith(".xml"):
                                        files.append(path)
				elif os.path.isfile(directory + folders):
					decompressed = check_file(directory, folders)
					if decompressed.endswith(".xml"):
						files.append(decompressed)
if len(results.files) > 0:
        fnames = results.files
        for f in fnames:
                files.append(f)

for fname in files:
        data = etree.parse(open(fname),xmlparser)
        root = data.getroot()

        filesize = os.path.getsize(fname)
        if filesize < SIZELIMIT:
                basicCheck = schema.xmlschema.validate(data)
                print "Basic Schema Check for " + str(fname) + ": " + str(basicCheck)
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
