import os

STREETSEGFIELDS = ["city","zip","street_direction","street_name","address_direction","start_house_number","end_house_number","odd_even_both"]
STREETSEGREQUIREDFIELDS = ["city","zip","street_name","start_house_number","end_house_number","odd_even_both"]

def streetsegCheck(tree, datafile):

	ferr = open(datafile + "streetseg.err","w")
	fwarn = open(datafile + "streetseg.warn","w")
	print "Checking street segment values...."
	
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
			for f in STREETSEGFIELDS:
				if f in tempmap and tempmap[f] != None:
					streetname += tempmap[f].strip() + "_"
				elif f in STREETSEGREQUIREDFIELDS:
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

	print "Finished checking street segment values, data located in " + datafile + "streetseg.err and " + datafile + "streeseg.warn"
	ferr.close()
	fwarn.close()
