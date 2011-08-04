import argparse, urllib, sys, os, re
from lxml import etree

baseSchemaUrl = "http://election-info-standard.googlecode.com/files/vip_spec_v"
version = "2.3"
versionList = ["2.0","2.1","2.2","2.3","3.0"]

zipcode = re.compile("\d{5}(?:[-\s]\d{4})?")
email = re.compile("[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]")
url = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))")
localityTypes = ['county','city','town','township','borough','parish','village','region']

parser = argparse.ArgumentParser(description='validate xml')

parser.add_argument('-s', action='store', dest='schema',
                    help='xsd schema to validate against xml document')

parser.add_argument('-v', action='store', dest='version',
                    help='xsd version used for validation')

parser.add_argument('-f', action='append', dest='files',
                    default=[], help='files to validate',)

results = parser.parse_args()

xmlparser = etree.XMLParser()

parsedschema = {}
intList = []
startHouseNum = -1
totalVotes = 0
sizelimit = 150000000
streetsegfields = ["city","zip","street_direction","street_name","address_direction"]
streetsegrequiredfields = ["city","zip","street_name"]

def checkIfRequired(subelem):
	if not("minOccurs" in subelem.attrib) or int(subelem.get("minOccurs"))>0:
		return "True"
	return "False"

def getXSVal(element): #removes namespace
	return element.tag.split('}')[-1]	

def setBaseVals(element):
	elemDict = {}
	elemDict["elements"] = []
	elemDict["type"] = getXSVal(element)
	elemDict["indicator"] = getXSVal(element[0])
	attributes = element[1:]
	if len(attributes) > 0:
		elemDict["attributes"] = []
	for a in attributes:
		elemDict["attributes"].append(a.attrib)	
	return elemDict	

def pullschema(data):
	xsdschema = {}	
	root = data.getroot()
	
	for elem in root:
		ename = elem.get("name")
		if ename == "votesWithCertification": #not actually used in the schema yet, when in use we'll have to make a special case for this
			continue
		xsdschema[ename] = {}
		if ename == "vip_object":
			vipelements = elem[0][0].getchildren()
			for vipe in vipelements:
				vipename = vipe.get("name")
				xsdschema[ename][vipename] = setBaseVals(vipe[0])
				indicator = xsdschema[ename][vipename]["indicator"]
				if indicator == "all":
					requiredlist = []
				vipsubelements = vipe[0][0].getchildren()
				xsdschema[ename][vipename]["elements"] = []
				for vipse in vipsubelements:
					if vipse.get("name") == None:
						vipse = vipse[0] 
					xsdschema[ename][vipename]["elements"].append(vipse.attrib)
					index = len(xsdschema[ename][vipename]["elements"])-1
					required = checkIfRequired(vipse)
					xsdschema[ename][vipename]["elements"][index]["required"] = required
					if required == "True" and indicator == "all":
						requiredlist.append(vipse.get("name"))
					if len(vipse) > 0:
						xsdschema[ename][vipename]["elements"][index]["attributes"] = "sort_order"
						xsdschema[ename][vipename]["elements"][index]["type"] = "xs:integer"
				if indicator == "all":
					xsdschema[ename][vipename]["requireds"] = requiredlist
					
		else:
			xsdschema[ename] = setBaseVals(elem)
			etype = xsdschema[ename]["type"]
			if etype == "complexType":
				requiredList = []
			children = elem[0].getchildren()
			for c in children:
				if etype == "complexType":
					xsdschema[ename]["elements"].append(c.attrib)		
					index = len(xsdschema[ename]["elements"])-1
					required = checkIfRequired(c)
					xsdschema[ename]["elements"][index]["required"] = required
					if etype=="complexType":
						requiredList.append(c.get("name"))
				else:
					xsdschema[ename]["elements"].append(c.get("value"))
			if etype == "complexType":
				xsdschema[ename]["requireds"] = requiredList
	return xsdschema

def getIntegerTypes(schema):
	ints = []
	for elem in schema:
		if elem == "vip_object":
			for vipe in schema[elem]:
				for i in range(len(schema[elem][vipe]["elements"])):
					if schema[elem][vipe]["elements"][i]["type"] == "xs:integer" and not(schema[elem][vipe]["elements"][i]["name"] in ints):
						ints.append(schema[elem][vipe]["elements"][i]["name"])
		elif schema[elem]["type"] == "complexType":
			for i in range(len(schema[elem]["elements"])):
				if schema[elem]["elements"][i]["type"] == "xs:integer" and not(schema[elem]["elements"][i]["name"] in ints):
					ints.append(schema[elem]["elements"][i]["name"])
	return ints

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
	if parent.get("id") == None:
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

def streetsegCheck(tree, datafile):

	filesize = os.path.getsize(datafile)
	ecount = 0
	wcount = 0
	streetmap = {}

	for elem in tree:
		if elem.tag == "street_segment":
			ident = elem.get("id")
			tempmap={}
		
			for se in elem:
				if se.tag == "non_house_address":
					for vals in se:
						tempmap[vals.tag] = vals.text
				else:
					tempmap[se.tag] = se.text
		
			streetname = ""
			for f in streetsegfields:
				if f in tempmap and tempmap[f] != None:
					streetname += tempmap[f].strip() + "_"
				elif f in streetsegrequiredfields:
					ferr.write("Error in street segment with ID '" + str(ident) + "' missing required '" + f + "'\n")
	
			streetname = streetname.rstrip("_").lower().replace(" ","_")
		
			streetside = tempmap["odd_even_both"]
		
			startnum = int(tempmap["start_house_number"])
			endnum = int(tempmap["end_house_number"])

			if not(streetname in streetmap):
				streetmap[streetname] = {}
			if not(streetside in streetmap[streetname]):
				streetmap[streetname][streetside] = []
			else:
				for i in range(len(streetmap[streetname][streetside])):
					tempstreet = streetmap[streetname][streetside][i]
					if (tempstreet["start_house"] <= startnum <= tempstreet["end_house"] or tempstreet["start_house"] <= endnum <= tempstreet["end_house"]):
						if tempstreet["precinct_id"] != tempmap["precinct_id"]:
							ferr.write("Error: House numbering error: Street Segments '" + str(tempstreet["id"]) + "' and '" + str(ident) + "' overlap house numbers and point to two different precincts\n")
							ecount += 1
						else:
							fwarn.write("Warning: House numbering overlaps but precinct IDs are consistent for Street Segments '" + str(tempstreet["id"]) + "' and '" + str(ident) + "'\n")
							wcount += 1	
			streetmap[streetname][streetside].append({"start_house":startnum, "end_house":endnum, "id":ident, "precinct_id":tempmap["precinct_id"]})
			if (ecount>5000 or wcount > 5000) and filesize > sizelimit:
				ferr.write("Too many warnings and/or errors to complete validation")
				fwarn.write("Too many warnings and/or errors to complete validation")
				break
	ferr.write("Error Count: " + str(ecount))
	fwarn.write("Warning Count: " + str(wcount))

def fullrequiredCheck():
	print "full required elements check"

if results.version:
	version = results.version
if version == "2.2":
	fschema = urllib.urlopen(baseSchemaUrl + version + "a.xsd")
else:
	fschema = urllib.urlopen(baseSchemaUrl + version + ".xsd")

xmlschema_doc = etree.parse(fschema)
xmlschema = etree.XMLSchema(xmlschema_doc)

fname = results.files[0]

data = etree.parse(open(fname),xmlparser)
root = data.getroot()
basicCheck = xmlschema.validate(data)

print "Basic Schema Check for " + str(fname) + ": " + str(basicCheck)

print "Creating dictionary of xml schema....."
parsedschema = pullschema(xmlschema_doc)
intList = getIntegerTypes(parsedschema)
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

ferr = open(fname + "streetseg.err","w")
fwarn = open(fname + "streetseg.warn","w")
print "Checking street segment values...."
streetsegCheck(root, fname)
print "Finished checking street segment values, data located in " + fname + "streetseg.err and " + fname + "streeseg.warn"
ferr.close()
fwarn.close()

if not(basicCheck):
	fullrequiredCheck()
