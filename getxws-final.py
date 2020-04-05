import csv
import urllib.request
import urllib.parse 
import os.path
from os import walk
import json

def yasbtoxws( url ):
    if len(url) > 0:
        newurl = url.replace( 'raithos.github.io', 'squad2xws.herokuapp.com/yasb/xws')

#        spliturl = urllib.parse.urlsplit(url)
 #       spliturl = list(spliturl)
  #      spliturl[1] = 'squad2xws.herokuapp.com'
   #     spliturl[2] = '/yasb/xws/'
    #    spliturl[3] = urllib.parse.quote(spliturl[3])
     #   spliturl[4] = urllib.parse.quote(spliturl[4])
      #  newurl = urllib.parse.urlunsplit(spliturl)

        with urllib.request.urlopen( newurl ) as response:
            return json.loads( response.read(),  encoding='UTF-8' )       


def savetoxws( path, row ):
    
    name = row[0]
    if len(name) == 0:
        name = row[1]
    cleanname = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ' or c=='_' or c=='(' or c ==')']).rstrip()
    filename = path + cleanname + '.json' 
    if not os.path.isfile( filename ):
        print('Saving ' + filename)
        j = {}
        j['VassalForm1'] = row[0]
        j['VassalForm2'] = row[1]
        j['Name'] = row[2]
        j['Discord'] = row[3]
        j['TTT'] = row[4]

        j['Option1'] = yasbtoxws(row[5])
        j['Option2'] = yasbtoxws(row[6])
        j['Drop'] = row[7]
        j['Add'] = row[8]
        j['Final'] = yasbtoxws(row[9])

        with open(filename, 'w', encoding='UTF-8') as xws:
            xws.write( json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')) )

def saverowtoxws( row ):
    savetoxws( './xws-final/', row )

# get all the XWS if we don't have them
with open('JTO Fully Correlated - Correlated.csv', 'r', encoding='UTF-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',' )
    next(reader)
    for row in reader:
        try:
            saverowtoxws(row)
        except urllib.error.HTTPError as err:
            print(err.url)
        except json.decoder.JSONDecodeError as err:
            print('JSONDecodeError for ' + row[0] + ' ' + row[1] )
            

# combine them all now
xwsfiles = []
for (dirpath, dirnames, filenames) in walk('./xws-final/'):
    for filename in filenames:
        xwsfiles.append ( os.path.join( dirpath, filename ) )

combined = []

for xwsfile in xwsfiles:
    with open(xwsfile,'r', encoding='UTF-8') as xws:
        combined.append(json.load(xws))

with open('combined-final.json', 'w', encoding='UTF-8') as output:
    output.write( json.dumps(combined, sort_keys=True, indent=4, separators=(',', ': '))) 
