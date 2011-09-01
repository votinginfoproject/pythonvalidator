import os, sys, urllib
from lxml import etree

class Schema:
    BASESCHEMAURL = "http://election-info-standard.googlecode.com/files/vip_spec_v"
    VERSIONLIST = ["2.0","2.1","2.2","2.3","3.0"]
    
    def __init__(self, createtype="version", createdata="2.3", versionlist=VERSIONLIST):	
        if createtype == "version" and createdata in versionlist:
            self.version = createdata
            schemafile = self.getSchemaFile() 
        elif createtype == "file" and os.path.exists(createdata):
            schemafile = open(createdata)
        else:
            print "Error creating Schema: Invalid type/version specified"
            sys.exit(0)  
	self.rawschema = etree.parse(schemafile)
	self.xmlschema = etree.XMLSchema(self.rawschema)
        self.schema = self.createSchema(self.rawschema) 
    def getSchemaFile(self, baseUrl=BASESCHEMAURL):
        if self.version == "2.2":
            fschema = urllib.urlopen(baseUrl + self.version + "a.xsd")
        else:
            fschema = urllib.urlopen(baseUrl + self.version + ".xsd")
        return fschema       
    def createSchema(self, data):
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
        def getXSVal(element): #removes namespace
	    return element.tag.split('}')[-1]
        def checkIfRequired(subelem):
	    if not("minOccurs" in subelem.attrib) or int(subelem.get("minOccurs"))>0:
		return "True"
	    return "False"
       
	xsdschema = {}	
	root = data.getroot()
	
	for elem in root:
		ename = elem.get("name")
		if ename == "votesWithCertification": #not actually used in the schema yet, when/if in use we'll have to make a special case for this
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
    def getIntegerTypes(self):
	schema = self.schema
	ints = []
	for elem in schema:
		if elem == "vip_object":
			for vipe in schema[elem]:
				vipelem = schema[elem][vipe]["elements"]
				for i in range(len(vipelem)):
					if vipelem[i]["type"] == "xs:integer" and not(vipelem[i]["name"] in ints):
						ints.append(vipelem[i]["name"])
		elif schema[elem]["type"] == "complexType":
			elements = schema[elem]["elements"]
			for i in range(len(elements)):
				if elements[i]["type"] == "xs:integer" and not(elements[i]["name"] in ints):
					ints.append(elements[i]["name"])
	return ints

 
    def __str__(self):
        return "Schema version: " + self.version + "\n Schema: " + str(self.schema)

if __name__ == '__main__':
    schema = Schema('version','3.0')
    print schema
    print "schema.rawschema: " + str(schema.rawschema)
    print "getIntegerTypes: " + str(schema.getIntegerTypes())
