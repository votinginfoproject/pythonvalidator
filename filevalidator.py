import argparse, urllib, sys, os, re, schema
from lxml import etree
from streetsegmentvalidator import streetsegCheck
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

def resetStartHouseNum():
	global startHouseNum
	startHouseNum = -1

def resetTotalVotes():
	global totalVotes
	totalVotes = 0

def setTotalVotes(votes):
	global totalVotes
	totalVotes = votes
	
def decrementVotes(votes):
	global totalVotes
	totalVotes = totalVotes - votes
	return totalVotes 

def printStartError(etag, parent):
	if parent.get("id") is None and parent.tag != "vip_object":
		parent = parent.getparent()
	return "'" + parent.tag + "' with attributes " + str(parent.attrib) + ": '" + str(etag) + "' "

def checkElement(elem, parent):
	if (len(elem.getchildren()) == 0 and (elem.text == None or len((elem.text).strip()) == 0)):
		fwarn.write("Warning: " + printStartError(elem.tag,parent) + "contains tag but the value is empty\n")
		return False
	elif(len(elem.getchildren()) == 0): #ending element
		if(elem.tag == "start_house_number"):
			try:
				global startHouseNum
				startHouseNum = int(elem.text) #can just use int here, since ints and longs were unified in python for the most part
			except:
				ferr.write("Error: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not numeric\n")
		elif(elem.tag == "end_house_number"):
			try:
				endHouseNum = int(elem.text)
				if(endHouseNum == 0):
					ferr.write("Error: " + printStartError(elem.tag,parent) + "cannot be zero, if ending house number is unknown enter a really large number such as 99999\n")
				elif(startHouseNum > -1 and endHouseNum < startHouseNum):
					ferr.write("Error: " + printStartError(elem.tag,parent) + "ending house number cannot be less than the starting house number\n")
			except:
				ferr.write("Error: '" + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not numeric\n")
		elif(elem.tag == "state" and len(elem.text) != 2):
			fwarn.write("Warning: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not a two letter abbreviation\n")
		elif(elem.tag == "zip" and not(zipcode.match(elem.text.strip()))):
			ferr.write("Error: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not a valid zipcode\n")
		elif(elem.tag == "email" and not(email.match(elem.text))):
			ferr.write("Error: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not a valid email\n")
		elif(elem.tag.find("url")>0 and not(url.match(elem.text))):
			fwarn.write("Warning: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which may be an invalid url\n")
		elif(parent.tag == "locality" and elem.tag == "type" and not((elem.text).lower() in localityTypes)):
			ferr.write("Error: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not a valid locality type\n")
		elif(parent.tag == "contest_result"):
			if(elem.tag == "total_votes"):
				setTotalVotes(int(elem.text))
			if(elem.tag == "total_valid_votes" or elem.tag == "overvotes"):
				decrementVotes(int(elem.text))
			if(elem.tag == "blank_votes"):
				if decrementVotes(int(elem.text))!=0:
					ferr.write("Error: " + printStartError("totalVotes",parent) + "is not equal to valid_votes + overvotes + blank_votes\n")
		elif elem.tag in intList:
			try:
				tempint = int(elem.text)
			except:
				ferr.write("Error: "  + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not numeric\n")
		return False	
	return True #otherwise, not an ending element

def semanticCheck(elem):
	if(elem.tag == "street_segment"):
		resetStartHouseNum()
	if(elem.tag == "contest_result"):
		resetTotalVotes()
	for subelem in elem:
		if not(checkElement(subelem, elem)):
			continue
		semanticCheck(subelem)

localityTypes = ['county','city','town','township','borough','parish','village','region']
sizelimit = 150000000

zipcode = re.compile("\d{5}(?:[-\s]\d{4})?")
email = re.compile("[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]")
url = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))")

xmlparser = etree.XMLParser()
startHouseNum = -1
totalVotes = 0

results = get_parsed_args()

if results.version:
	version = results.version

fname = results.files[0]

data = etree.parse(open(fname),xmlparser)
root = data.getroot()

schema = schema.Schema("version",version)
basicCheck = schema.xmlschema.validate(data)

print "Basic Schema Check for " + str(fname) + ": " + str(basicCheck)

print "Creating dictionary of xml schema....."
intList = schema.getIntegerTypes()
print "Finished pulling schema"

ferr = open(fname + ".err","w")
fwarn = open(fname + ".warn","w")	
ferr.write("Errors for " + fname + "\n")
ferr.write("******************************************\n")	
fwarn.write("Warnings for " + fname + "\n")
fwarn.write("******************************************\n")	
print "Checking file semantics...."
semanticCheck(root)
print "Finished checking file semantics, data located in " + fname + ".err and " + fname + ".err"
ferr.close()
fwarn.close()

streetsegCheck(root, fname)

if not(basicCheck):
	fullrequiredCheck(root,schema.schema,fname)
