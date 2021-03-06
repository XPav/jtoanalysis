from os import walk
import json
import os
import csv
import urllib.request


ships = {}
pilots = {}
upgrades = {}
allpilots = {}
allupgrades = {}

addremovedupgrades = {}

def CountUpgrades( l ):
    theseupgrades = {}
    for p in l['pilots']:
        if 'upgrades' in p and len(p['upgrades']) > 0:
            for u in p['upgrades'].values():
                for u2 in u:
                    if u2 in theseupgrades:
                        theseupgrades[u2] += 1
                    else:
                        theseupgrades[u2] = 1
    return theseupgrades
           

def GetCostValue( cost, pdata, sdata ):
    if 'value' in cost:
        return cost['value']
    elif cost['variable'] == 'initiative':
        return cost['values'][str(pdata['initiative'])]
    else:
        for stat in sdata['stats']:
            if 'type' in stat and stat['type'] == cost['variable']:
                return cost['values'][str(stat['value'])]

def LoadShip( pilots, upgrades, ship, listid, faction, rank ):
    oship = {}

    pilotid = p['id']
    if pilotid == 'bossk-z-95headhunter':
        pilotid = 'bossk-z95af4headhunter'

    # one line per ship
    pdata = pilots[pilotid]
    allpilots[pilotid]['count'] += 1

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
    oship['rank'] = rank
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
                allupgrades[u]['count'] += 1

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
                    if ('device' in upgrade and upgrade['device']['type'] == 'Bomb') or 'bomb' in u:
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

                # Missing Actions
                useless |= ('ability' in upgrade and 'Attack ([Lock])' in upgrade['ability'] and not 'Lock' in actiontype)
                useless |= ('ability' in upgrade and 'Attack ([Focus])' in upgrade['ability'] and not 'Focus' in actiontype)
                useless |= (u == 'perceptivecopilot' and not 'Focus' in actiontype)
                useless |= (u == 'bazemalbus' and not 'Focus' in actiontype)
                useless |= (u == 'r3astromech' and not 'Lock' in actiontype)
                useless |= (u == 'firecontrolsystem' and not 'Lock' in actiontype)

                # Added actions that did nothing
                useless |= (u == 'squadleader' and 'Coordinate' in originalactions )
                useless |= (u == 'targetingcomputer' and 'Lock' in originalactions )

                # Require Shields
                useless |= (u in [ 'gnkgonkdroid', 'inertialdampeners', 'r2d2-crew', 'r2astromech', 'r2d2' ] and shields == 0)

                # Because SF has free linked rotate
                useless |= (u == 'agilegunner' and sdata['xws'] == 'tiesffighter' ) 

                # Arcs
                useless |= (u == 'outmaneuver' and not 'Front Arc' in arcs)
                useless |= (u == 'veterantailgunner' and not 'Rear Arc' in arcs)
                useless |= (u in [ 'hotshotgunner', 'agilegunner', 'bistan', 'hansolo'] and (not 'Single Turret Arc' in arcs and not 'Double Turret Arc' in arcs))

                # Arcs or bombs
                useless |= (u == 'paigetico' and (not 'Single Turret Arc' in arcs and not 'Double Turret Arc' in arcs) and (bombcount == 0) )

                # Upgrades that rely on or help other upgrades
                useless |= (u == 'jabbathehutt' and illicits == 0)
                useless |= (u == 'havoc' and astromechs == 0 and sensors == 0 )
                useless |= (u == 'xg1assaultconfiguration' and cannons == 0 )
                useless |= (u in [ 'andrasta', 'genius', 'delayedfuses', 'cadbane', 'skilledbombardier' ] and devicecount == 0)
                useless |= (u in [ 'saturationsalvo', 'munitionsfailsafe', 'os1arsenalloadout', 'instinctiveaim' ] and torpsmissiles == 0)
                useless |= (u == 'trajectorysimulator' and bombcount == 0)

                if useless:
                    oship[f'useless{uselesscount:02d}'] = u
                    uselesscount += 1
                    oship['uselesscost'] += GetCostValue( upgrades[u]['cost'], pdata, sdata )

    oship['uselesscount'] = uselesscount

    return oship

for (dirpath, dirnames, filenames) in walk('../xwing-data2/data/pilots'):
    for filename in filenames:
        with open(os.path.join(dirpath,filename),'r') as f:
            j = json.load(f)
            ships[j['xws']] = j

            for p in j['pilots']:
                xws = p['xws']
                pilots[xws] = p
                allpilots[ p['xws'] ] = { 'name': xws, 'type': 'pilot', 'count': 0, 'limited': p['limited'], 'slots' :'', 'added' : 0, 'removed': 0 }

for (dirpath, dirnames, filenames) in walk('../xwing-data2/data/upgrades'):
    for filename in filenames:
        with open(os.path.join(dirpath,filename),'r') as f:
            j = json.load(f)
            for u in j:
                xws = u['xws']
                upgrades[xws] = u
                slots = ''
                for side in u['sides']:
                    for slot in side['slots']:
                        slots += (slot + ' ')
                allupgrades[xws] = { 'name': xws, 'type': 'upgrade', 'count': 0, 'limited': u['limited'], 'slots' : slots, 'added' : 0, 'removed': 0 }

with open('jto.json', 'r', encoding='UTF-8') as f:
    combined = json.load( f )     

oships = []
olists = {}

# One line per list
for l in combined['tournament']['players']:
    if  len(l['list']) > 0:
        shipcount = 0
        init = 0

        olist = {}
        olist['name'] = l['name']
        olist['wins'] = 0
        olist['byes'] = 0
        olist['rank'] = l['rank']['elimination']
        olist['faction'] = l['list']['faction']
        olist['points'] = l['list']['points']
        olist['totalhealth'] = 0
        olist['totalmainattack'] = 0
        olist['totalagility'] = 0
        olist['totalupgradecount'] = 0
        olist['totaluselesscount'] = 0
        olist['totaluselesscost'] = 0
        olist['shipcount'] = 0
        
        for p in l['list']['pilots']:
            oship = LoadShip( pilots, upgrades, p, olist['name'], olist['faction'], olist['rank'] )
            oships.append(oship)

            init = init + oship['initiative']
            olist['totalhealth'] += (oship['hull'] +  oship['shields'])
            olist['totalmainattack'] += oship['attack']
            olist['totalagility'] += oship['agility']
            olist['totalupgradecount'] += oship['upgradecount']
            olist['totaluselesscount'] += oship['uselesscount']
            olist['totaluselesscost'] += oship['uselesscost']

            olist['shipcount'] += 1

        olist['handicap'] = 200 - olist['points'] + olist['totaluselesscost']
        olist['avginitiative'] = init / olist['shipcount']

        listbuilder = l['list']['vendor']
        if len(listbuilder) == 0:
            print('no builder url for ' + l['name'] )
        elif 'yasb' in listbuilder:
            olist['url'] = listbuilder['yasb']['link']
        elif 'lbn' in listbuilder:
            olist['url'] = listbuilder['lbn']['link']
        elif 'sb2xws' in listbuilder:
            olist['url'] = listbuilder['sb2xws']['url']
        else:
            print('')

        olists[l['name']] = olist

for r in combined['tournament']['rounds']:
    if int(r['round-number']) > 32:
        for match in r['matches']:
            if match['result'] == 'bye':
                olists[match['player1']]['byes'] += 1
            if match['result'] == 'win':
                if 'winner' in match:
                    olists[match['player1']]['wins'] += 1
                else:
                    if match['player1points'] > match['player2points']:
                        olists[match['player1']]['wins'] += 1
                    else:
                        olists[match['player2']]['wins'] += 1

with open('lists-during.csv', 'w', newline='', encoding='UTF-8') as csvfile:
    lists = list(olists.values())
    writer = csv.DictWriter(csvfile, fieldnames=[*olist])
    writer.writeheader()
    writer.writerows(lists)

with open('ships-during.csv', 'w', newline='', encoding='UTF-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[*oship])
    writer.writeheader()
    writer.writerows(oships)





