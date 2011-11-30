import urllib
import schema
import sqlite3
import argparse
import MySQLdb as mdb

#default settings: 
#	database_type:	sqlite3
#	database_name:	vip
#	host:		localhost
#	username:	username
#	password:	password

#cursor needs to be a script level variable since other mysqldb does not have 'execute script' we will have to execute every table create statement individually
#TODO:Add connection stuff for postgres

def get_parsed_args():
	parser = argparse.ArgumentParser(description='create database from schema')

	parser.add_argument('-d', action='store', dest='database_type',
			help='database type to use, valid types are: sqlite3, mysql, postgres')

	parser.add_argument('-u', action='store', dest='username',
			help='username to access the database')
	
	parser.add_argument('-p', action='store', dest='password',
			help='password for the database user')

	parser.add_argument('-n', action='store', dest='database_name',
			help='database name the data is stored in')

	parser.add_argument('-host', action='store', dest='host',
			help='host address for the database, with sqlite3 assumes a local db and this is the database file location')

	return parser.parse_args()

database_type = "sqlite3"
database_name = "vip"
host = "localhost"
username = "username"
password = "password"

parameters = get_parsed_args()

fschema = urllib.urlopen("http://election-info-standard.googlecode.com/files/vip_spec_v3.0.xsd")
schema = schema.Schema(fschema)

complex_types = schema.getElementData("complexType")
simple_types = schema.getElementData("simpleType")

data = schema.getElementData("element")["vip_object"]

#based on the database_type, create the correct connection type, use the same cursor for all stuff since all types use the same object

create_statement = ""

TYPES = {"sqlite3":{"id":"TEXT", "xs:string":"TEXT", "xs:integer":"INTEGER", "xs:dateTime":"TEXT", "xs:date":"TEXT"}, "mysql":{"id":"VARCHAR(16)", "xs:string":"VARCHAR(256)", "xs:integer":"BIGINT", "xs:dateTime":"DATETIME", "xs:date":"DATE"}, "postgres":{"id":"VARCHAR(16)", "xs:string":"VARCHAR(256)", "xs:dateTime":"TIMESTAMP", "xs:date":"DATE"}} 

if database_type == "sqlite3":
	connection = sqlite3.connect("localhost")
elif database_type == "mysql":
	connection = mdb.connect(host, username, password, database_name)

cursor = connection.cursor()

#should rewrite this as a function accepting the elements, to create the original table and then the complex type tables

def element_create(data):
	create_statement = ""
	for element in data:
		create_statement = "CREATE TABLE " + str(element["name"]) + " (id " + TYPES[database_type]["id"] + " PRIMARY KEY, element_id " + TYPES[database_type]["xs:integer"]
		for e in element["elements"]:
			if e["name"] == "None":
				continue
			elif e["type"].startswith("xs:"):
				create_statement += ", " + str(e["name"]) + " " + TYPES[database_type][e["type"]]
			else:
				if e["type"] in simple_types:
					create_statement += ", " + str(e["name"])
					if database_type == "sqlite3":
						create_statement += " TEXT"
					elif database_type == "mysql":
						create_statement += " ENUM("
						for e_type in simple_types[e["type"]]["elements"]:
							create_statement += "'" + e_type + "',"
						create_statement = create_statement[:-1] + ")" #remove trailing ',' from ENUM
				elif e["type"] in complex_types:
					create_statement += ", " + str(e["name"]) + "_id " + TYPES[database_type]["xs:integer"]
					#could add the foeign key stuff for postgres and mysql
		create_statement += ");"		
		print create_statement
		cursor.execute(create_statement)		
	return create_statement

def complex_create(data):
	create_statement = ""
	for element in data:
		create_statement = "CREATE TABLE " + str(element) + " (id " 
		if database_type == "sqlite3":
			create_statement += "INTEGER PRIMARY KEY AUTOINCREMENT"
		elif database_type == "mysql":
			create_statement += "BIGINT PRIMARY KEY AUTO_INCREMENT"
		for e in data[element]["elements"]:
			if e["name"] == "None":
				continue
			elif e["type"].startswith("xs:"):
				create_statement += ", " + str(e["name"]) + " " + TYPES[database_type][e["type"]]
			else:
				if e["type"] in simple_types:
					create_statement += ", " + str(e["name"])
					if database_type == "sqlite3":
						create_statement += " TEXT"
					elif database_type == "mysql":
						create_statement += " ENUM("
						for e_type in simple_types[e["type"]]["elements"]:
							create_statement += e_type + ","
						create_statement = create_statement[:-1] + ")" #remove trailing ',' from ENUM
				elif e["type"] in complex_types:
					create_statement += ", " + str(e["name"]) + "_id " + TYPES[database_type]["xs:integer"]
		create_statement += ");"
		cursor.execute(create_statement)		
	return create_statement

element_create(data["elements"])
complex_create(complex_types)

connection.commit()
