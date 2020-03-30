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
                    if stat['value'] > attack:
                        attack = stat['value']
                if stat['type'] == 'agility':
                    agility += stat['value']
                if stat['type'] == 'hull':
                    hull += stat['value']
                if stat['type'] == 'shields':
                    shields += stat['value']

            # Todo: add hull/shield upgrades
            
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
    init = 0

    olist = {}
    olist['totalhealth'] = 0
    olist['totalattack'] = 0
    olist['totalagility'] = 0
    olist['upgradecount'] = 0
    olist['shipcount'] = 0

    for p in l['xws']['pilots']:
        oship = {}
        oship['listid'] = l['name'] + '#' + str(l['number'])
        oship['faction'] =l['xws']['faction'] 
        oship['yasb'] = l['yasb']

        olist.update( oship )

        for f in fields:
            oship[f] = p[f]

        for u in p['upgrades']:
            olist['upgradecount'] += 1

        init = init + oship['initiative']
        olist['totalhealth'] += (p['hull'] +  p['shields'])
        olist['totalattack'] += p['attack']
        olist['totalagility'] += p['agility']

        oships.append(oship)

        olist['shipcount'] += 1

    olist['avginitiative'] = init / olist['shipcount']

    olists.append(olist)

with open('ships.csv', 'w', newline='') as csvfile:
    fieldnames = ['listid', 'faction', 'yasb' ]
    fieldnames.extend(fields)

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for os in oships:
        writer.writerow(os)

with open('lists.csv', 'w', newline='') as csvfile:
    lfieldnames = ['listid', 'faction', 'shipcount', 'upgradecount', 'totalagility', 'totalattack', 'totalhealth', 'avginitiative', 'yasb'  ]

    writer = csv.DictWriter(csvfile, fieldnames=lfieldnames)
    writer.writeheader()
    for ol in olists:
        writer.writerow(ol)

 


