import csv
import urllib.request
import os.path

def savetoxws( filename, yasburl ):
    if not os.path.isfile(filename):
        with open(filename, 'wb') as xws:
            print(f'saving {filename} from {yasburl}')
            newurl = yasburl.replace( 'raithos.github.io', 'squad2xws.herokuapp.com/yasb/xws')
            with urllib.request.urlopen( newurl ) as response:
                xws.write( response.read() )


def saverowtoxws( row ):
    savetoxws( './xws/' + row[0] + ' 1.json', row[1] )
    savetoxws( './xws/' + row[0] + ' 2.json', row[2] )

with open('responses.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',' )
    for row in reader:
        saverowtoxws(row)
