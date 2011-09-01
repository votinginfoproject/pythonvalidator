import argparse, urllib, sys, os, re, schema
from lxml import etree

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

def streetsegCheck(tree, datafile):

	filesize = os.path.getsize(datafile)
	ecount = 0
	wcount = 0
	streetmap = {}
	streetError = False

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
					streetError = True
	
			if streetError:
				streetError = False
				continue

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

def getTags(elements):
	tags = []
	for e in elements:
		tags.append(e.tag)
	return tags

def checkType(elem, elemtype, schema):
	taglist = getTags(elem)
	requiredList = schema[elemtype]["requireds"]
	for k in range(len(requiredList)):
		if not(requiredList[k] in taglist):
			return False
	return True

def fullrequiredCheck(root, schema):
	for vipelem in root:
		ident = vipelem.get("id")
		if schema["vip_object"][vipelem.tag]["indicator"] == "all":
			children = vipelem.getchildren()
			childrenTags = getTags(children)
			requiredList = schema["vip_object"][vipelem.tag]["requireds"]
			for i in range(len(schema["vip_object"][vipelem.tag]["elements"])):
				if schema["vip_object"][vipelem.tag]["elements"][i]["name"] in requiredList:
					if not(schema["vip_object"][vipelem.tag]["elements"][i]["name"] in childrenTags):
						ferr.write("Error '" + vipelem.tag + "' ID:" + str(ident) + " missing " + schema["vip_object"][vipelem.tag]["elements"][i]["name"] + "\n")
					elif schema["vip_object"][vipelem.tag]["elements"][i]["type"][0:3] != "xs:" and schema[schema["vip_object"][vipelem.tag]["elements"][i]["type"]]["type"] == "complexType":
						for c in children:
							if schema["vip_object"][vipelem.tag]["elements"][i]["name"] == c.tag:
								if not(checkType(c,schema["vip_object"][vipelem.tag]["elements"][i]["type"],schema)):
									ferr.write("Error '" + vipelem.tag + "' ID:" + str(ident) + " missing field in '" + schema["vip_object"][vipelem.tag]["elements"][i]["name"] + "'\n")
								break
		else:
			children = vipelem.getchildren()
			j = 0
			for i in range(len(schema["vip_object"][vipelem.tag]["elements"])):
				if j >= len(children):
					if schema["vip_object"][vipelem.tag]["elements"][i]["required"] == "True":
						ferr.write("Error '" + vipelem.tag + "' ID:" + str(ident) + " missing " + schema["vip_object"][vipelem.tag]["elements"][i]["name"]+"\n")
						break 
				elif schema["vip_object"][vipelem.tag]["elements"][i]["name"] == children[j].tag:
					if schema["vip_object"][vipelem.tag]["elements"][i]["type"][0:3] != "xs:":
						if not(checkType(children[j],schema["vip_object"][vipelem.tag]["elements"][i]["type"][0:3])):
							ferr.write("Error '" + vipelem.tag + "' ID:" + str(ident) + " missing field in '" + schema["vip_object"][vipelem.tag]["elements"][i]["name"] + "'\n")
							break
					j+=1
				elif schema["vip_object"][vipelem.tag]["elements"][i]["required"] == "True":
					ferr.write("Error '" + vipelem.tag + "' ID:" + str(ident) + " missing " + schema["vip_object"][vipelem.tag]["elements"][i]["name"] + "\n")
					break

baseSchemaUrl = "http://election-info-standard.googlecode.com/files/vip_spec_v"
version = "2.3"
versionList = ["2.0","2.1","2.2","2.3","3.0"]
localityTypes = ['county','city','town','township','borough','parish','village','region']
sizelimit = 150000000
streetsegfields = ["city","zip","street_direction","street_name","address_direction","start_house_number","end_house_number","odd_even_both"]
streetsegrequiredfields = ["city","zip","street_name","start_house_number","end_house_number","odd_even_both"]

zipcode = re.compile("\d{5}(?:[-\s]\d{4})?")
email = re.compile("[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]")
url = re.compile("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))")

xmlparser = etree.XMLParser()
parsedschema = {}
intList = []
startHouseNum = -1
totalVotes = 0

results = get_parsed_args()

if results.version:
	version = results.version
if version == "2.2":
	fschema = urllib.urlopen(baseSchemaUrl + version + "a.xsd")
else:
	fschema = urllib.urlopen(baseSchemaUrl + version + ".xsd")

schema = schema.Schema("version","2.3")

fname = results.files[0]

data = etree.parse(open(fname),xmlparser)
root = data.getroot()
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

ferr = open(fname + "streetseg.err","w")
fwarn = open(fname + "streetseg.warn","w")
print "Checking street segment values...."
streetsegCheck(root, fname)
print "Finished checking street segment values, data located in " + fname + "streetseg.err and " + fname + "streeseg.warn"
ferr.close()
fwarn.close()

if not(basicCheck):
	print "Running full check on required xml fields"
	ferr = open(fname + "fullerrors.err","w")
	fullrequiredCheck(root,schema.schema)
	print "Finished full required xml field check, data located in " + fname + "fullerrors.err"
	ferr.close()
