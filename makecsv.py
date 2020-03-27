from os import walk
import json
import os
import csv

ships = {}
pilots = {}

for (dirpath, dirnames, filenames) in walk('../xwing-data2/data/pilots'):
    for filename in filenames:
        with open(os.path.join(dirpath,filename),'r') as f:
            j = json.load(f)
            ships[j['xws']] = j

            for p in j['pilots']:
                pilots[p['xws']] = p


# Add stuff to the data
with open('combined.json', 'r') as combinedf:
    combined = json.load(combinedf)
    for l in combined:
        for p in l['xws']['pilots']:
            pdata = pilots[p['id']]

            shipid = p['ship']
            if shipid == 'upsilonclasscommandshuttle':
                shipid = 'upsilonclassshuttle' 

            sdata = ships[shipid]

            p['initiative'] = pdata['initiative']

            hull = 0
            shields = 0
            agility = 0
            attack = 0

            for stat in sdata['stats']:
                if stat['type'] == 'attack':
                    attack += stat['value']
                if stat['type'] == 'agility':
                    agility += stat['value']
                if stat['type'] == 'hull':
                    hull += stat['value']
                if stat['type'] == 'shields':
                    shields += stat['value']

            # Todo: add upgrades

            p['agility'] = agility
            p['hull'] = hull
            p['shields'] = shields
            p['attack'] = attack

fields = [ 'id', 'ship', 'points', 'initiative', 'agility','hull', 'shields', 'attack' ]

oships = []
olists = []

# One line per
for l in combined:
    shipcount = 0
    upgradecount = 0
    init = 0
    health = 0
    
    olist = {}
    for p in l['xws']['pilots']:
        oship = {}
        oship['listid'] = l['name'] + '#' + str(l['number'])
        oship['faction'] =l['xws']['faction'] 
        oship['yasb'] = l['yasb']
        olist = oship.copy()

        for f in fields:
            oship[f] = p[f]

        for u in p['upgrades']:
            upgradecount += 1

        init = init + oship['initiative']

        oships.append(oship)

        shipcount += 1
    olist['shipcount'] = shipcount
    olist['upgradecount'] = upgradecount
    olist['avginitiative'] = init / shipcount

    olists.append(olist)

with open('ships.csv', 'w', newline='') as csvfile:
    fieldnames = ['listid', 'faction', 'yasb' ]
    fieldnames.extend(fields)

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for os in oships:
        writer.writerow(os)

with open('lists.csv', 'w', newline='') as csvfile:
    lfieldnames = ['listid', 'faction', 'shipcount', 'upgradecount', 'avginitiative', 'yasb'  ]

    writer = csv.DictWriter(csvfile, fieldnames=lfieldnames)
    writer.writeheader()
    for ol in olists:
        writer.writerow(ol)

 


