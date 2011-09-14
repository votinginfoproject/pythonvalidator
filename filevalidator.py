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
sizelimit = 150000000

xmlparser = etree.XMLParser()
version = "2.3"

results = get_parsed_args()

if results.version:
	version = results.version

if version == "2.2":
	fschema = urllib.urlopen(BASESCHEMAURL + version + "a.xsd")
else:
	fschema = urllib.urlopen(BASESCHEMAURL + version + ".xsd")

fname = results.files[0]

data = etree.parse(open(fname),xmlparser)
root = data.getroot()

schema = schema.Schema(fschema)

basicCheck = schema.xmlschema.validate(data)

print "Basic Schema Check for " + str(fname) + ": " + str(basicCheck)

semanticCheck(root, schema, fname)

root = data.getroot()

streetsegCheck(fname)

#if not(basicCheck):
#	fullrequiredCheck(root,schema.schema,fname)
