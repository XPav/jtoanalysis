from os import walk
import json
import os
import csv
import urllib.request


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

def LoadShip( pilots, upgrades, ship, listid, faction ):
    oship = {}

    pilotid = p['id']
    if pilotid == 'bossk-z-95headhunter':
        pilotid = 'bossk-z95af4headhunter'

    # one line per ship
    pdata = pilots[pilotid]

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

    originalactions = actiontype.copy()

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

    oship['name'] = listid
    oship['faction'] = faction
    oship['id'] = pdata['xws']
    oship['ship'] = sdata['xws']
    oship['points'] = ship['points']

    oship['upgradecount'] = 0

    devicecount = 0
    bombcount = 0
    torpsmissiles = 0
    illicits = 0
    astromechs = 0
    cannons = 0
    sensors = 0
    
    oship['uselesscount'] = 0
    oship['uselesscost'] = 0

    for s in range(0,10):
        oship[f'upgrade{s:02d}'] = ''

    upgradecount = 0
    if 'upgrades' in p:
        for slot in p['upgrades']:
            if slot in ['torpedo', 'missile']:
                torpsmissiles += 1
            for u in p['upgrades'][slot]:
                upgrade = upgrades[u]['sides'][0]
                oship[f'upgrade{upgradecount:02d}'] = u
                upgradecount += 1
                oship['upgradecount'] = upgradecount
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
                if 'Device' in upgrade['slots']:
                    devicecount += 1
                    if 'device' in upgrade and upgrade['device']['type'] == 'Bomb':
                        bombcount += 1
                if 'Illicit' in upgrade['slots']:
                    illicits += 1
                if 'Astromech' in upgrade['slots']:
                    astromechs += 1
                if 'Cannon' in upgrade['slots']:
                    cannons += 1
                if 'Sensor' in upgrade['slots']:
                    sensors += 1

    oship['agility'] = agility
    oship['hull'] = hull
    oship['shields'] = shields
    oship['attack'] = attack
    oship['initiative'] = pdata['initiative']

    # Go find useless upgrades
    for s in range(0,4):
        oship[f'useless{s:02d}'] = ''

    uselesscount = 0
    if 'upgrades' in p:
        for slot in p['upgrades']:
            for u in p['upgrades'][slot]:
                useless = False
                upgrade = upgrades[u]['sides'][0]

                useless |= (u in [ 'delayedfuses', 'skilledbombardier', 'andrasta', 'genius' ] and bombcount == 0)
                useless |= (u == 'cadbane' and devicecount == 0)
                useless |= (u == 'perceptivecopilot' and not 'Focus' in actiontype)
                useless |= (u == 'bazemalbus' and not 'Focus' in actiontype)
                useless |= (u == 'r3astromech' and not 'Lock' in actiontype)
                useless |= (u == 'firecontrolsystem' and not 'Lock' in actiontype)
                useless |= ('ability' in upgrade and 'Attack ([Lock])' in upgrade['ability'] and not 'Lock' in actiontype)
                useless |= ('ability' in upgrade and 'Attack ([Focus])' in upgrade['ability'] and not 'Focus' in actiontype)
                useless |= (u in [ 'gnkgonkdroid', 'inertialdampeners', 'r2d2-crew' ] and shields == 0)
                useless |= (u in [ 'saturationsalvo', 'munitionsfailsafe', 'os1arsenalloadout', 'instinctiveaim' ] and torpsmissiles == 0)

                if u in [ 'hotshotgunner', 'agilegunner', 'bistan', 'hansolo']:
                    if not 'Single Turret Arc' in arcs and not 'Double Turret Arc' in arcs:
                        useless = True

                useless |= (u == 'outmaneuver' and not 'Front Arc' in arcs)
                useless |= (u == 'veterantailgunner' and not 'Rear Arc' in arcs)
                useless |= (u == 'agilegunner' and sdata['xws'] == 'tiesffighter' ) 

                if u == 'paigetico':
                    if not 'Single Turret Arc' in arcs and not 'Double Turret Arc' in arcs: 
                        useless = True
                    if bombcount == 0:
                        useless = True

                useless |= (u == 'jabbathehutt' and illicits == 0)

                useless |= (u =='squadleader' and 'Coordinate' in originalactions )
                useless |= (u =='targetingcomputer' and 'Lock' in originalactions )
                useless |= (u =='havoc' and astromechs == 0 and sensors == 0 )
                useless |= (u =='xg1assaultconfiguration' and cannons == 0 )



                if useless:
                    oship[f'useless{uselesscount:02d}'] = u
                    uselesscount += 1
                    oship['uselesscost'] = GetCostValue( upgrades[u]['cost'], pdata, sdata )

    oship['uselesscount'] = uselesscount

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


with urllib.request.urlopen( 'https://tabletop.to/jank-tank-open/listjuggler' ) as response:
    combined = json.loads( response.read() )     
    with open('jto.json', 'w') as f:
        f.write( json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')) )

oships = []
olists = []

# One line per list
for l in combined['tournament']['players']:
    if len(l['list']) > 0:
        if not 'yasb' in l['list']['vendor']:
            print('No YASB ' + l['name'])
        shipcount = 0
        init = 0

        olist = {}
        olist['name'] = l['name']
        olist['faction'] = l['list']['faction']
        olist['totalhealth'] = 0
        olist['totalmainattack'] = 0
        olist['totalagility'] = 0
        olist['totalupgradecount'] = 0
        olist['totaluselesscount'] = 0
        olist['totaluselesscost'] = 0
        olist['shipcount'] = 0

        for p in l['list']['pilots']:
            oship = LoadShip( pilots, upgrades, p, olist['name'], olist['faction'] )
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

        olists.append(olist)
    else:
        print('BAD LIST ' + l['name'])

with open('lists-final.csv', 'w', newline='', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[*olist])
    writer.writeheader()
    for ol in olists:
        writer.writerow(ol)

with open('ships-final.csv', 'w', newline='', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[*oship])
    writer.writeheader()
    for os in oships:
        writer.writerow(os)




