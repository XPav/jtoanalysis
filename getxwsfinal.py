import csv
import urllib.request
import os.path
from os import walk
import json

def savetoxws( path, vassal, discord, yasburl ):
    if len(yasburl) > 0:

        cleanname = "".join([c for c in vassal if c.isalpha() or c.isdigit() or c==' ' or c=='_' or c=='(' or c ==')']).rstrip()

        filename = path + cleanname + '.json' 
        if not os.path.isfile( filename ):
            with open(filename, 'w') as xws:
                print(f'saving {filename} from {yasburl}')
                newurl = yasburl.replace( 'raithos.github.io', 'squad2xws.herokuapp.com/yasb/xws')

                j = {}
                j['name'] = vassal
                j['discord'] = discord
                j['yasb'] = yasburl

                with urllib.request.urlopen( newurl ) as response:
                    j['xws'] = json.loads( response.read() )       

                xws.write( json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')) )

def saverowtoxws( row ):
    savetoxws( './xws-final/', row[0], row[1], row[2] )


# get all the XWS if we don't have them
with open('finallists.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',' )
    next(reader)
    for row in reader:
        saverowtoxws(row)

# combine them all now
xwsfiles = []
for (dirpath, dirnames, filenames) in walk('./xws-final/'):
    for filename in filenames:
        xwsfiles.append ( os.path.join( dirpath, filename ) )


combined = []

for xwsfile in xwsfiles:
    with open(xwsfile,'r') as xws:
        #name = os.path.splitext( os.path.basename(xwsfile) )[0]
        #name = name.replace('#', '_')
        combined.append(json.load(xws))

with open('combined-final.json', 'w') as output:
    output.write( json.dumps(combined, sort_keys=True, indent=4, separators=(',', ': '))) 
