import re, os, schema

LOCALITYTYPES = ['county','city','town','township','borough','parish','village','region']

zipcode = re.compile("\d{5}(?:[-\s]\d{4})?")
email = re.compile("[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]")
url = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))")

startHouseNum = -1
totalVotes = 0

def setIntTypes(schema):
	global intList
	intList = schema.getAllTypeElements("xs:integer")

def setErrorWarningFiles(basename, fulldir):
	global ferr, fwarn
	ferr = open(fulldir + "/" + basename + ".semanticerr", "w")
	fwarn = open(fulldir + "/" + basename + ".semanticwarn","w")

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
	else:
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
		elif(parent.tag == "locality" and elem.tag == "type" and not((elem.text).lower() in LOCALITYTYPES)):
			ferr.write("Error: " + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not a valid locality type\n")
		elif(parent.tag == "contest_result"):
			if(elem.tag == "total_votes"):
				setTotalVotes(int(elem.text))
			elif(elem.tag == "total_valid_votes" or elem.tag == "overvotes"):
				decrementVotes(int(elem.text))
			elif(elem.tag == "blank_votes") and decrementVotes(int(elem.text))!=0:
				ferr.write("Error: " + printStartError("totalVotes",parent) + "is not equal to valid_votes + overvotes + blank_votes\n")
		elif elem.tag in intList:
			try:
				int(elem.text)
			except:
				ferr.write("Error: "  + printStartError(elem.tag,parent) + "is '" + elem.text + "' which is not numeric\n")

def findElements(elem):
	if(elem.tag == "street_segment"):
		resetStartHouseNum()
	elif(elem.tag == "contest_result"):
		resetTotalVotes()
	for subelem in elem:
		if len(subelem.getchildren()) == 0: #ending element
			checkElement(subelem, elem)
			subelem.clear()
			while subelem.getprevious() is not None:
				del subelem.getparent()[0]
		else:
			findElements(subelem)
	elem.clear()
	while elem.getprevious() is not None:
		del elem.getparent()[0]

def semanticCheck(root, schema, basename, fulldir):
	setIntTypes(schema)
	setErrorWarningFiles(basename, fulldir)
	print "Checking file semantics for " + basename
	findElements(root)
	print "Finished checking file semantics for " + basename
	ferr.close()
	fwarn.close()
