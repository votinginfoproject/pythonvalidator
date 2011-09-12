import urllib
from lxml import etree

class Schema:
    
    def __init__(self, schemafile):	
        if schemafile is None:
            print "Error creating Schema: Invalid schema file used"
            sys.exit(0)  
	
	self.rawschema = etree.parse(schemafile)
	self.xmlschema = etree.XMLSchema(self.rawschema)
        self.schema = self.createSchema(self.rawschema) 
    
    def createSchema(self, data):
	def getXSVal(element): #removes namespace
		return element.tag.split('}')[-1]

	def checkIfRequired(subelem, indicator):
		if (indicator == "all" or indicator == "sequence") and (not("minOccurs" in subelem.attrib) or int(subelem.get("minOccurs"))>0):
			return True
		if indicator == "choice" and ("minOccurs" in subelem.attrib) and int(subelem.get("minOccurs"))>0:
			return True
		return False

	def createSimpleContent(childelem):
		childDict = {}
		subchildren = childelem.getchildren()
		for subchild in subchildren:
			childDict[subchild.get("name")] = subchild.attrib
		return childDict

	def createComplexSimple(elem):
		elemDict = {}
		eindicator = getXSVal(elem[0])		
		elemDict["indicator"] = eindicator
	
		if eindicator == "all":
			elemDict["requireds"] = []
			elemDict["elements"] = [] 
			counter = 0 
		elif eindicator == "restriction":
			elemDict["base"] = elem[0].get("base")
			elemDict["elements"] = []
	
		children = elem[0].getchildren()
		for child in children: 
			if eindicator == "simpleContent":
				elemDict["attributes"] = createSimpleContent(child)
			elif eindicator == "restriction":
				elemDict["elements"].append(child.get("value"))
			else:
				elemDict["name"] = elem.get("name")
				elemDict["elements"].append(child.get("name"))
				elemDict["elements"][counter] = {}
				if len(child.getchildren()) > 0:
					elemDict["elements"][counter] = getElements(child)
				else:
					elemDict["elements"][counter] = child.attrib
				if checkIfRequired(child,eindicator):
					elemDict["requireds"].append(child.get("name"))
				counter += 1
		return elemDict

	def createElement(elem):
		elemDict = {}
		etype = getXSVal(elem[0])
		eindicator = getXSVal(elem[0][0])
		elemDict["type"] = etype
		elemDict["indicator"] = eindicator 

		if eindicator != "simpleContent":
			elemDict["elements"] = []
			elemDict["requireds"] = []
			counter = 0
		
		children = elem[0][0].getchildren()
		for child in children: 
			if eindicator == "simpleContent":
				elemDict["attributes"] = createSimpleContent(child) 
				elemDict["name"] = child.get("name")
			else:
				elemDict["name"] = elem.get("name")
				elemDict["elements"].append(child.get("name"))
				elemDict["elements"][counter] = {}
				if len(child.getchildren()) > 0:
					elemDict["elements"][counter] = createElement(child)
				else:
					elemDict["elements"][counter] = child.attrib
				if checkIfRequired(child,eindicator):
					elemDict["requireds"].append(child.get("name"))
				counter += 1
		return elemDict
   
	xsdschema = {}	
	root = data.getroot()
	
	for elem in root:
		ename = elem.get("name")
		etype = getXSVal(elem)
	
		if not etype in xsdschema:
			xsdschema[etype] = {}
		if etype == "element":
			xsdschema[etype][ename] = createElement(elem)
		else:
			xsdschema[etype][ename] = createComplexSimple(elem)
	return xsdschema
	
    def getAllTypeElements(self, typename):
	elemlist = []
	for elements in self.schema:
		if elements == "simpleType":
			elemlist.extend(self.getSimpleElements(self.schema[elements], typename))
		elif elements == "complexType" or elements == "element":
			elemlist.extend(self.getFirstLevelElements(self.schema[elements], typename))
	return list(set(elemlist))

    def getTypeElementsWithinBase(self, typename, basetype):
	elemlist = []
	for elements in self.schema:
		if elements == "simpleType" and basetype == elements:
			elemlist.extend(self.getSimpleElements(self.schema[elements], typename))
		elif (elements == "complexType" or elements == "element") and basetype == elements:
			elemlist.extend(self.getFirstLevelElements(self.schema[elements], typename))
	return list(set(elemlist))

    def getSimpleElements(self, elements, typename):
	elemList = []
	for element in elements:
		if elements[element]["base"] == typename:
			elemlist.append(element)
	return elemList

    def getSequenceElements(self, elements, typename):
	elemlist = []
	for i in range(len(elements)):
		if "elements" in elements[i]:
			elemlist.extend(self.getSequenceElements(elements[i]["elements"], typename))
		elif "type" in elements[i] and elements[i]["type"] == typename:
			elemlist.append(elements[i]["name"])
	return elemlist

    def getFirstLevelElements(self, elements, typename):
	elemlist = []
	for element in elements:
		if "elements" in elements[element]:
			elemlist.extend(self.getSequenceElements(elements[element]["elements"], typename))
		elif "type" in elements[element] and elements[element]["type"] == typename:
			elemlist.append(element)
	return elemlist

    def getElementData(self, elementname):
	for element in self.schema:
		if element == elementname:
			return self.schema[element]
		elif element == "simpleType":
			temp = self.searchSimpleElements(self.schema[element], elementname)
			if temp:
				return temp
		elif element == "complexType" or element == "element":
			temp = self.searchFirstLevelElements(self.schema[element], elementname)
			if temp:
				return temp

    def searchSimpleElements(self, elements, elementname):
	for element in elements:
		if element == elementname:
			return elements[element] 

    def searchSequenceElements(self, elements, typename):
	for i in range(len(elements)):
		if "name" in elements[i] and elements[i]["name"] == typename:
			return elements[i]
		elif "elements" in elements[i]:
			tempval = self.searchSequenceElements(elements[i]["elements"], typename)
			if tempval is not None:
				return tempval

    def searchFirstLevelElements(self, elements, typename):
	for element in elements:
		if "name" in elements[element] and elements[element]["name"] == typename:
			return elements[element]
		elif "elements" in elements[element]:
			tempval = self.searchSequenceElements(elements[element]["elements"], typename)
			if tempval is not None:
				return tempval

    def __str__(self):
        return "Schema: " + str(self.schema)

if __name__ == '__main__':
    fschema = urllib.urlopen("http://election-info-standard.googlecode.com/files/vip_spec_v2.3.xsd")

    schema = Schema(fschema)

    print schema
    print "schema.rawschema: " + str(schema.rawschema)
    print "schema.getAllTypeElements: " + str(schema.getAllTypeElements("xs:integer"))
    print "schema.getTypeElementsWithinBase: " + str(schema.getTypeElementsWithinBase("xs:integer", "simpleType"))
    print "schema.getTypeElementsWithinBase: " + str(schema.getTypeElementsWithinBase("xs:integer", "complexType"))
    print "schema.getElementData: " + str(schema.getElementData("street_segment"))
