import schema

def setErrorFile(fname):
	global ferr
	ferr = open(fname + "fullerrors.err", "w")

def setComplexTypes(schema):
	global complexTypes
	complexTypes = schema.getElementData("complexType")
	for ctype in complexTypes:
		complexTypes[ctype]["elementsoftype"] = schema.getTypeElementsWithinBase(ctype, "element")
		complexTypes[ctype]["elementnames"] = getElementNameList(complexTypes[ctype]["elements"])

def getElementNameList(elements):
	namelist = []
	for element in elements:
		if "name" in element:
			namelist.append(element["name"])
	return namelist

def getElementTypeData(tag, schema):
	data = schema.getElementDataWithinBase(tag, "element")
	data["elementnames"] = getElementNameList(data["elements"])
	return data

def checkAllBasic(children, elementid, elementnames):
	childlist = []
	for child in children:
		if not child.tag in elementnames:
			ferr.write("Error: Element with ID '" + str(elementid) + "' contains extra subelement '" + child.tag + "'\n")
		elif child.text is not None and len(child.tag.strip()) > 0:
			childlist.append(child.tag)
		elif len(child.getchildren()) > 0:
			childlist.append(child.tag)
			for ctype in complexTypes:
				if child.tag in complexTypes[ctype]["elementsoftype"]:
					checkComplex(child.getchildren(), elementid, ctype)
	return childlist

def checkComplexBasic(elements, elementid, ctype):
	childlist = []
	for element in elements:
		if not element.tag in complexTypes[ctype]["elementnames"]:
			ferr.write("Error: Element with ID '" + str(elementid) + "' contains extra subelement '" + element.tag + "'\n")
		elif element.text is not None and len(element.tag.strip()) > 0:
			childlist.append(element.tag)
	return childlist

def checkRequired(childlist, elementid, requireds):
	for element in requireds:
		if not element in childlist:
			ferr.write("Error: Element with ID '" + str(elementid) + "' missing '" + element + "'\n")

def checkComplex(elements, elementid, ctype):
	childlist = checkComplexBasic(elements, elementid, ctype)
	checkRequired(childlist, elementid, complexTypes[ctype]["requireds"])

def checkAll(children, elementid, elementData):
	if elementid == '991034307676':
		print children
		print children[5].getchildren()
	childlist = checkAllBasic(children, elementid, elementData["elementnames"])
	checkRequired(childlist, elementid, elementData["requireds"])

def checkSequence(children, elementid, elementData):
	j = 0
	for i in range(len(elementData["elements"])):
		if j >= len(children):
			if elementData["elements"][i]["name"] in elementData["requireds"]:
				ferr.write("Error: Element '" + str(elementData["name"]) + "' with ID '" + str(elementid) + "' missing '" + elementData["elements"][i]["name"] + "'\n")
		elif elementData["elements"][i]["name"] == children[j].tag:
			if elementData["elements"][i]["type"] in complexTypes:
				checkComplex(children[j].getchildren(), elementid, elementData["elements"][i]["type"])
			j+=1
		elif elementData["elements"][i]["name"] in elementData["requireds"]:
			ferr.write("Error: Element '" + str(elementData["name"]) + "' with ID '" + str(elementid) + "' missing '" + elementData["elements"][i]["name"] + "'\n")

def checkData(root, schema):
	elementTypeData = {}
	for element in root:
		elementid = element.get("id")
		children = element.getchildren()
		if elementid == '991034307676':
			print children
			print children[5].getchildren()
	
		if not "name" in elementTypeData or elementTypeData["name"] != element.tag:
			elementTypeData = getElementTypeData(element.tag, schema)
		if elementTypeData["indicator"] == "all":
			checkAll(children, elementid, elementTypeData)
		else:
			checkSequence(children, elementid, elementTypeData)
			
def fullrequiredCheck(root, schema, fname):
	setErrorFile(fname)
	setComplexTypes(schema)

	print "Running full check on required xml fields"
	
	checkData(root, schema)

	print "Finished full required xml field check, data located in " + fname + "fullerrors.err"
	ferr.close()
