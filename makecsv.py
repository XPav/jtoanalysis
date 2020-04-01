from os import walk
import json
import os
import csv

ships = {}
pilots = {}
upgrades = {}

def LoadShip( pilots, upgrades, ship, listid, faction, yasb ):
    oship = {}
    # one line per ship
    pdata = pilots[p['id']]

    # workround for upsilon
    shipid = p['ship']
    if shipid == 'upsilonclasscommandshuttle':
        shipid = 'upsilonclassshuttle' 

    # base ship data
    sdata = ships[shipid]

    # base other data
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

    oship['listid'] = listid
    oship['faction'] = faction
    oship['id'] = pdata['xws']
    oship['ship'] = sdata['xws']
    oship['points'] = ship['points']

    oship['upgradecount'] = 0
    for slot in p['upgrades']:
        for u in p['upgrades'][slot]:
            upgrade = upgrades[u]['sides'][0]
            oship['upgradecount'] += 1
            if 'grants' in upgrade:
                for g in upgrade['grants']:
                    if g['type'] == 'stat':
                        if g['value'] == 'attack':
                            attack += g['amount']
                        if g['value'] == 'agility':
                            agility += g['amount']
                        if g['value'] == 'hull':
                            hull += g['amount']
                        if g['value'] == 'shields':
                            shields += g['amount']

    oship['agility'] = agility
    oship['hull'] = hull
    oship['shields'] = shields
    oship['attack'] = attack
    oship['initiative'] = pdata['initiative']

    oship['yasb'] = yasb

    return oship


for (dirpath, dirnames, filenames) in walk('../xwing-data2/data/pilots'):
    for filename in filenames:
        with open(os.path.join(dirpath,filename),'r') as f:
            j = json.load(f)
            ships[j['xws']] = j

            for p in j['pilots']:
                pilots[p['xws']] = p

for (dirpath, dirnames, filenames) in walk('../xwing-data2/data/upgrades'):
    for filename in filenames:
        with open(os.path.join(dirpath,filename),'r') as f:
            j = json.load(f)
            for u in j:
                upgrades[u['xws']] = u

# Add stuff to the data
with open('combined.json', 'r') as combinedf:
    combined = json.load(combinedf)


oships = []
olists = []

# One line per list
for l in combined:
    shipcount = 0
    init = 0

    olist = {}
    olist['listid'] = l['name'] + '#' + str( l['number'])
    olist['faction'] = l['xws']['faction']
    olist['totalhealth'] = 0
    olist['totalmainattack'] = 0
    olist['totalagility'] = 0
    olist['totalupgradecount'] = 0
    olist['shipcount'] = 0

    for p in l['xws']['pilots']:
        oship = LoadShip( pilots, upgrades, p, olist['listid'], olist['faction'], l['yasb'] )
        oships.append(oship)

        init = init + oship['initiative']
        olist['totalhealth'] += (oship['hull'] +  oship['shields'])
        olist['totalmainattack'] += oship['attack']
        olist['totalagility'] += oship['agility']
        olist['totalupgradecount'] += oship['upgradecount']

        olist['shipcount'] += 1

    olist['avginitiative'] = init / olist['shipcount']
    olist['yasb'] = l['yasb']

    olists.append(olist)

with open('ships.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[*oship])
    writer.writeheader()
    for os in oships:
        writer.writerow(os)

with open('lists.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[*olist])
    writer.writeheader()
    for ol in olists:
        writer.writerow(ol)

 


