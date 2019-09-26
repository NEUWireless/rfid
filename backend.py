import serial, io, json
from time import time
ser = serial.Serial('/dev/ttyUSB0', 9600)

FILENAME = "attendance.json"



def main():
	
	people_ex = { 						# structure of the people dictionary
	"FFFFFFFF" 	: {	"name" 	: str(),
					"times"	: list()
					}
	}
	
	people = dict()  # create an empty dict in case there is nothing to load
	
	try :
		people = load()
	except FileNotFoundError :
		save(people)
		
		
	id = ser.readline().decode("utf-8")[:-2]  # trim the newline character
	if id in people :
		people[id]["times"].append(time())
		save(people)
		return {"name" : people[id]["name"], "uid" : id, "recognized" : "yes"}
		
		# no further action needed from server, person already exists
		
	else : 
		new_person(id, "test name")
		return {"name" : "" , "uid" : id, "recognized" : "no"}
		# server needs to get a name to go with id

def new_person(id, name):  # add a new person to the file w/ name, id, and time
	
	people = dict()
	
	try :
		people = load()
	except FileNotFoundError :
		save(people)
	
	people[id] = {	"name" 	: name,
					"times"	: [time()]
					}
	save(people)
	
	
def save(data):  ## data should be a dictionary
	
	with open(FILENAME, "w+") as file :
		file.write(json.dumps(data))
	
def load():
	try :
		with open(FILENAME) as file :
			return json.loads(file.read())
	except json.decoder.JSONDecodeError :
		return {} # unreadable file
	
if __name__ == "__main__":
	main()