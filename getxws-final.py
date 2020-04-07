import csv
import urllib.request
import urllib.parse 
import os.path
from os import walk
import json

def yasbtoxws( url ):
    if len(url) > 0:
        newurl = url.replace( 'raithos.github.io', 'squad2xws.herokuapp.com/yasb/xws')

        with urllib.request.urlopen( newurl ) as response:
            return json.loads( response.read(),  encoding='UTF-8' )       

ttt = {}

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

        if row[4] in ttt:
            if 'list' in ttt[row[4]]:
                j['Final'] = ttt[row[4]]['list']
                with open(filename, 'w', encoding='UTF-8') as xws:
                    xws.write( json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')) )
            else:
                print('No list for ' + row[4])
        else:
            print('Who is ' + row[4])

    if row[4] in ttt:
        del ttt[ row[4] ]

def saverowtoxws( row ):
    savetoxws( './xws-final/', row )

with open(  'jto.json', 'r', encoding='UTF-8') as tttf:
    tttj = json.load( tttf )
    for player in tttj['tournament']['players']:
        ttt[ player['name'] ] = player

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
