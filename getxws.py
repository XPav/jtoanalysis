import csv
import urllib.request
import os.path
from os import walk
import json

def savetoxws( path, name, number, yasburl ):
    if len(yasburl) > 0:

        cleanname = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ' or c=='_' or c=='(' or c ==')']).rstrip()

        filename = path + cleanname + ' ' + str(number) + '.json' 
        if not os.path.isfile( filename ):
            with open(filename, 'w') as xws:
                print(f'saving {filename} from {yasburl}')
                newurl = yasburl.replace( 'raithos.github.io', 'squad2xws.herokuapp.com/yasb/xws')

                j = {}
                j['name'] = cleanname
                j['number'] = number
                j['yasb'] = yasburl

                with urllib.request.urlopen( newurl ) as response:
                    j['xws'] = json.loads( response.read() )       

                xws.write( json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')) )

def saverowtoxws( row ):
    savetoxws( './xws/', row[0], 1, row[2] )
    savetoxws( './xws/', row[0], 2, row[4] )


# get all the XWS if we don't have them
with open('Jank Tank Open Squad Options - By Order Sign Up.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',' )
    next(reader)
    for row in reader:
        saverowtoxws(row)

# combine them all now
xwsfiles = []
for (dirpath, dirnames, filenames) in walk('./xws/'):
    for filename in filenames:
        xwsfiles.append ( os.path.join( dirpath, filename ) )


combined = []

for xwsfile in xwsfiles:
    with open(xwsfile,'r') as xws:
        #name = os.path.splitext( os.path.basename(xwsfile) )[0]
        #name = name.replace('#', '_')
        combined.append(json.load(xws))

with open('combined.json', 'w') as output:
    output.write( json.dumps(combined, sort_keys=True, indent=4, separators=(',', ': '))) 
