from os import walk
import json
import os
import csv

ships = {}
pilots = {}
upgrades = {}

def GetCostValue( cost, pdata, sdata ):
    if 'value' in cost:
        return cost['value']
    elif cost['variable'] == 'initiative':
        return cost['values'][str(pdata['initiative'])]
    else:
        pass

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

    allactions = sdata['actions']
    if 'shipActions' in pdata:
        allactions = pdata['shipActions']

    actiontype = []
    for action in allactions:
        actiontype.append( action['type'] )

    hull = 0
    shields = 0
    agility = 0
    attack = 0

    arcs = []

    for stat in sdata['stats']:
        if stat['type'] == 'attack':
            if stat['value'] > attack:
                attack = stat['value']
            arcs.append( stat['arc'] )
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

    devicecount = 0
    bombcount = 0
    torpsmissiles = 0

    oship['uselesscount'] = 0
    oship['uselesscost'] = 0

    for slot in p['upgrades']:
        if slot in ['torpedo', 'missile']:
            torpsmissiles += 1
        for u in p['upgrades'][slot]:
            upgrade = upgrades[u]['sides'][0]
            oship['upgradecount'] += 1
            # Adjust stats
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
                    if g['type'] == 'action':
                        actiontype.append( g['value']['type'] ) 
            if 'attack' in upgrade:
                arcs.append( upgrade['attack']['arc'])
            # Keep track of things for uselessness
            if "Device" in upgrade['slots']:
                devicecount += 1
                if 'device' in upgrade and upgrade['device']['type'] == 'Bomb':
                    bombcount += 1
            
            

    oship['agility'] = agility
    oship['hull'] = hull
    oship['shields'] = shields
    oship['attack'] = attack
    oship['initiative'] = pdata['initiative']

    # Go find useless upgrades

    for slot in p['upgrades']:
        for u in p['upgrades'][slot]:
            useless = False
            upgrade = upgrades[u]['sides'][0]

            useless |= (u in [ 'delayedfuses', 'skilledbombardier', 'andrasta', 'genius' ] and bombcount == 0)
            useless |= (u == 'cadbane' and devicecount == 0)
            useless |= (u == 'perceptivecopilot' and not 'Focus' in actiontype)
            useless |= (u == 'bazemalbus' and not 'Focus' in actiontype)
            useless |= (u == 'r3astromech' and not 'Lock' in actiontype)
            useless |= ('ability' in upgrade and 'Attack ([Lock])' in upgrade['ability'] and not 'Lock' in actiontype)
            useless |= ('ability' in upgrade and 'Attack ([Focus])' in upgrade['ability'] and not 'Focus' in actiontype)
            useless |= (u in [ 'gnkgonkdroid', 'inertialdampeners', 'r2d2-crew' ] and shields == 0)
            useless |= (u in [ 'saturationsalvo', 'munitionsfailsafe', 'os1arsenalloadout', 'instinctiveaim' ] and torpsmissiles == 0)

            if u in [ 'hotshotgunner', 'agilegunner', 'bistan', 'hansolo']:
                if not 'Single Turret Arc' in arcs and not 'Double Turret Arc' in arcs:
                    useless = True

            if useless:
                oship['uselesscount'] += 1
                oship['uselesscost'] = GetCostValue( upgrades[u]['cost'], pdata, sdata )

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
    olist['totaluselesscount'] = 0
    olist['totaluselesscost'] = 0
    olist['shipcount'] = 0

    for p in l['xws']['pilots']:
        oship = LoadShip( pilots, upgrades, p, olist['listid'], olist['faction'], l['yasb'] )
        oships.append(oship)

        init = init + oship['initiative']
        olist['totalhealth'] += (oship['hull'] +  oship['shields'])
        olist['totalmainattack'] += oship['attack']
        olist['totalagility'] += oship['agility']
        olist['totalupgradecount'] += oship['upgradecount']
        olist['totaluselesscount'] += oship['uselesscount']
        olist['totaluselesscost'] += oship['uselesscost']

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

 


