import os
from lxml import etree

STREETSEGFIELDS = ["city","zip","street_direction","street_name","street_suffix","address_direction","start_house_number","end_house_number","odd_even_both"]
STREETNAMEFIELDS = ["city","zip","street_direction","street_name","street_suffix","address_direction"]
STREETSEGREQUIREDFIELDS = ["city","zip","street_name","start_house_number","end_house_number","odd_even_both"]

def getStreetName(elementmap, ssid):
	streetname = ""
	for field in STREETSEGFIELDS:
		if field in elementmap and elementmap[field] is not None:
			if field in STREETNAMEFIELDS:
				streetname += elementmap[field] + "_"
		elif field in STREETSEGREQUIREDFIELDS:
			ferr.write("Error in street segment with ID '" + str(ssid) + "' missing required '" + field + "'\n")
			return False
	return streetname.rstrip("_").lower().replace(" ","_")

def getFields(elements):
	elementmap = {}
		
	for element in elements:
		if element.tag == "non_house_address":
			elementmap.update(getFields(element))
		else:
			elementmap[element.tag] = element.text.strip()
	return elementmap

def getNewStreetData(streetfields, ssid):
	streetdata = {}
	streetdata["startnum"] = int(streetfields["start_house_number"])
	streetdata["endnum"] = int(streetfields["end_house_number"])
	streetdata["id"] = ssid
	streetdata["precinct_id"] = streetfields["precinct_id"]
	streetdata["errors"] = []
	streetdata["warnings"] = []
	streetdata["duplicates"] = []
	return streetdata

def validateStreetSegments(context):

	streetmap = {}
	
	for event, elem in context:

		ssid = elem.get("id") 
		streetfields = getFields(elem)
		streetname = getStreetName(streetfields, ssid)

		if not streetname:
			continue
		
		streetside = streetfields["odd_even_both"]
		
		newstreet = getNewStreetData(streetfields, ssid)
		
		if not(streetname in streetmap):
			streetmap[streetname] = {}
		if not(streetside in streetmap[streetname]):
			streetmap[streetname][streetside] = []
			streetmap[streetname][streetside].append(newstreet)
		else:
			for i in range(len(streetmap[streetname][streetside])):
				checkstreet = streetmap[streetname][streetside][i]
				if (checkstreet["startnum"] <= newstreet["startnum"] <= checkstreet["endnum"] or checkstreet["startnum"] <= newstreet["endnum"] <= checkstreet["endnum"]):
					if checkstreet["precinct_id"] != newstreet["precinct_id"]:
						newstreet["errors"].append(checkstreet["id"])
					elif checkstreet["startnum"] == newstreet["startnum"] and checkstreet["endnum"] == newstreet["endnum"]:
						streetmap[streetname][streetside][i]["duplicates"].append(newstreet["id"])
						break
					else:
						newstreet["warnings"].append(checkstreet["id"])
			streetmap[streetname][streetside].append(newstreet)

		elem.clear()
		while elem.getprevious() is not None:
			del elem.getparent()[0]

	writeErrors(streetmap)

def writeErrors(streetmap):
	
	for streetname in streetmap:
		for streetside in streetmap[streetname]:
			for i in range(len(streetmap[streetname][streetside])):
				streetdata = streetmap[streetname][streetside][i]
				if len(streetdata["errors"]) > 0:
					ferr.write("Error: Street Segment '" + str(streetdata["id"]) + "' overlaps house numbers and points to different precints in the following street segments: ")
					for i in range(len(streetdata["errors"])):
						ferr.write(str(streetdata["errors"][i]) + ", ")
					ferr.write("\n")
				if len(streetdata["warnings"]) > 0:
					fwarn.write("Warning: Street Segment '" + str(streetdata["id"]) + "' overlaps house numbers but points the same precints in the following street segments: ")
					for i in range(len(streetdata["warnings"])):
						fwarn.write(str(streetdata["warnings"][i]) + ", ")
					fwarn.write("\n")
				if len(streetdata["duplicates"]) > 0:
					fdup.write("Duplicate: Street Segment '" + str(streetdata["id"]) + "' is duplicated " + str(len(streetdata["duplicates"])) + " time(s) with the following street segements: ")
  					for i in range(len(streetdata["duplicates"])):
						fdup.write(str(streetdata["duplicates"][i]) + ", ")
					fdup.write("\n")
	ferr.close()
	fwarn.close()
	fdup.close()

def setErrorWarningFiles(fname):
	global ferr, fwarn, fdup
	ferr = open(fname + "streetseg.err", "w")
	fwarn = open(fname + "streetseg.warn","w")
	fdup = open(fname + "streetseg.dup", "w")

def streetsegCheck(fname):
	setErrorWarningFiles(fname)

	print "Validating street segments...."
	context = None
	with open(fname) as xml_doc:
		context = etree.iterparse(xml_doc, tag="street_segment")

		if context is None:
			next

		validateStreetSegments(context)
	print "Finished validating street segments, data located in " + fname + ".err, " + fname + ".warn, and " + fname + ".dup"
