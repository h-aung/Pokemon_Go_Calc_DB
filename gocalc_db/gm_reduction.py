#!/usr/bin/env python

### This module deals with building the database for any further use. 
### This includes downloading Gamemaster from pokeminer, reducing gamemaster to database, and 
### old features of making database for silph cups. 

import sys, os
import json
import pickle
import numpy as np
from .db import DB
import sqlite3
#from six.moves import urllib
import six

sqlite3.register_adapter(np.int64, int)

def get_gm_url():
    with open('data/GMlink.txt','r') as f:
        url = f.read()
    print( url)
    return

def update_gm(url=None,dbno=False,cup=True,debug=False, max_level=51, no_download = False):
    if not no_download:
        #download file
        print( "    Downloading lastest Game Master file ... ")
        if url==None:
            url = 'https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json'
            #url = 'https://raw.githubusercontent.com/pokemongo-dev-contrib/'+\
            #'pokemongo-game-master/master/versions/latest/GAME_MASTER.json'
        filedata = six.moves.urllib.request.urlopen(url)
        data = filedata.read()
        with open('data/GAME_MASTER.json','wb') as f:
            f.write(data)
        with open('data/GMlink.txt','w') as f:
            f.write(url)
    #open files
    with open('data/arr.pkl', 'rb') as f:
         arr = pickle.load(f)
    
    #emergency update
    os.system(r'sed -i -e "s/\"vfxName\": \"myst_fire\"/\"vfxName\": \"mystical_fire\"/g" data/GAME_MASTER.json')
    with open('data/GAME_MASTER.json') as f:
        data = json.load(f)
    
    #database initialization
    DB.close_database()
    os.remove("data/example.db")
    print( "    Reducing the downloaded Game Master file ... ")
    conn = sqlite3.connect('data/example.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE type
                 (id int PRIMARY KEY, 
                 name text)''')
    c.execute('''CREATE TABLE pokemon
                 (id int PRIMARY KEY, 
                 dexid int,
                 name text, 
                 atk int, 
                 def int, 
                 sta int, 
                 type1 int,
                 type2 int,
                 bcr real, 
                 rarity text,
                 FOREIGN KEY(type1) REFERENCES type(id),
                 FOREIGN KEY(type2) REFERENCES type(id)
                 )''')
    c.execute('''CREATE TABLE move
                 (id int PRIMARY KEY, 
                 name text, 
                 d int, 
                 e int, 
                 t int, 
                 pvpd int, 
                 pvpe int, 
                 pvpt int, 
                 type int,
                 FOREIGN KEY(type) REFERENCES type(id)
                 )''')
    c.execute('''CREATE TABLE pk_move
                 (pk_id int, 
                 move_id int, 
                 PRIMARY KEY(pk_id,move_id),
                 FOREIGN KEY(pk_id) REFERENCES pokemon(id),
                 FOREIGN KEY(move_id) REFERENCES move(id)
                 )''')
    c.execute('''CREATE TABLE eff
                 (atk int, 
                 def int,
                 eff real,
                 PRIMARY KEY(atk,def),
                 FOREIGN KEY(atk) REFERENCES type(id),
                 FOREIGN KEY(def) REFERENCES type(id)
                 )''')
    c.execute('''CREATE TABLE cup
                     (ind int PRIMARY KEY, 
                     name text,
                     id int,
                     FOREIGN KEY(id) REFERENCES pokemon(id))''')
    item_name = "data"#"itemTemplate"#"itemTemplates"
    pokemon = {item_name:[]} #temp array to store pokemon
    eff = {item_name:[]}
    movei = 1
    movearr = [] #temp array to store moves
    dat = pickle.load(open('data/type_arr.pkl','rb'))
    dat = dat+['pokemon_type_none']
    if debug:
        print(dat)
    for i in range(len(dat)):
        dat[i] = dat[i].lower()
        c.execute("INSERT INTO type VALUES(?,?)",(i+1,dat[i]))
        
    #database names
    pokemon_name = "pokemonSettings"#"pokemon"#
    move_name = "moveSettings"#"move"#
    
    #loop and separate
    for i in range(len(data)):
    #for item in data[item_name]:
        item = data[i][item_name]
        temp = item.keys()
        if pokemon_name in temp:
            pokemon[item_name].append(item)
        if "combatMove" in temp:
            aura_wheel_repalcement = {406:"aura_wheel_electric", 407:"aura_wheel_dark"}
            if isinstance(item["combatMove"]["uniqueId"], int):
                combatmove_name = aura_wheel_repalcement[item["combatMove"]["uniqueId"]]
            else:
                combatmove_name = item["combatMove"]["uniqueId"].lower()
            if debug:
                print(combatmove_name)
            if "power" in item["combatMove"]:
                dmg = item["combatMove"]["power"]
            else:
                dmg = 0
            if "energyDelta" in item["combatMove"]:
                e = item["combatMove"]["energyDelta"]
            else:
                e = 0
            if (e>0) and ("_fast" not in combatmove_name):
                combatmove_name = combatmove_name+"_fast"
            if "durationTurns" in item["combatMove"]:
                turn = item["combatMove"]["durationTurns"]+1
            else:
                turn = 1
            c.execute("INSERT INTO move VALUES(?, ?, NULL, NULL, NULL, ?, ?, ?, NULL)",
                (movei,combatmove_name,dmg,
                e, turn))
            movearr.append(combatmove_name)
            movei +=1 #checked
        if move_name in temp:
            if isinstance(item[move_name]["movementId"], int):
                combatmove_name = aura_wheel_repalcement[item[move_name]["movementId"]]
            else:
                combatmove_name = item[move_name]["movementId"].lower()
            if "power" in item[move_name]:
                dmg = item[move_name]["power"]
            else:
                dmg = 0
            if "energyDelta" in item[move_name]:
                e = item[move_name]["energyDelta"]
            else:
                e = 0
            if (e>0) and ("_fast" not in combatmove_name):
                combatmove_name = combatmove_name+"_fast"
            typeid = dat.index(item[move_name]["pokemonType"].lower())+1
            c.execute("UPDATE move SET d = ?, e = ?, t = ?, type = ? WHERE name = ?",
                (dmg, e, item[move_name]["durationMs"], typeid, combatmove_name))
        if "pokemonUpgrades" in temp:
            stardust = item["pokemonUpgrades"]["stardustCost"]
        if "playerLevel" in temp:
            cpmulti = item["playerLevel"]["cpMultiplier"]
        if "typeEffective" in temp:
            typeid = dat.index(item["templateId"].lower())+1
            multilist = item["typeEffective"]["attackScalar"]
            for i in range(18):
                c.execute("INSERT INTO eff VALUES(?,?,?)",(typeid,i+1,multilist[i]))
    typeid = dat.index("pokemon_type_none")+1
    for i in range(18):
        c.execute("INSERT INTO eff VALUES(?,?,?)",(i+1,typeid,1.0))
        #eff[item_name].append(item)
    poki = 1
    megai = 0
    ignored_form = set(['pikachu', 'vivillon', 'flabebe', 'floette', 'florges', 'furfrou','scatterbug','spewpa', 'morpeko',\
                    'koraidon', 'miraidon', 'keldeo', 'latios', 'latias', 'snorlax']) ##temp fix for snorlax
    subfix_form = set(["normal","2019","2020","2021","2022","2023","2024"])
    special_moves = {"dialga_origin":"roar_of_time","palkia_origin":"spacial_rend",\
    "necrozma_dawn_wings":"moongeist_beam","necrozma_dusk_mane":"sunsteel_strike"}
    for item in pokemon[item_name]:
        pok_name = item[pokemon_name]["pokemonId"].lower()
        if debug:
            print(pok_name)
        ### alola, galarian, hisuian, a(armor), paldea, castform (prefix, not suffix), deoxys ==, burmy, wormadam==, 
        ### ignore: pikachu, vivillon, flabebe, floette, florges, furfrou
        if "form" in item[pokemon_name]:
            if pok_name in ignored_form:
                continue
            form = item[pokemon_name]["form"].lower()
            if any(substr in form for substr in subfix_form):
                continue
            
        else:
            form=pok_name
        if item[pokemon_name]["familyId"] == "FAMILY_HONEDGE":
            continue
        dexid = int((item["templateId"].split('_'))[0][1:])
        
        if "shadowBaseCaptureRate" in item[pokemon_name]["encounter"]: #checked
            bcr = item[pokemon_name]["encounter"]["shadowBaseCaptureRate"] ### temporary, re-check
        else:
            bcr = 0.0
        type1id = dat.index(item[pokemon_name]["type"].lower())+1
        if "pokemonClass" in item[pokemon_name]:
            if item[pokemon_name]["pokemonClass"]=='POKEMON_CLASS_LEGENDARY':
                rarity = 'l'
            elif item[pokemon_name]["pokemonClass"]=='POKEMON_CLASS_MYTHIC':
                rarity = 'm'
            elif item[pokemon_name]["pokemonClass"]=='POKEMON_CLASS_ULTRA_BEAST':
                rarity = 'u'
        else:
            rarity = None
        if "type2" in item[pokemon_name]:
            type2id = dat.index(item[pokemon_name]["type2"].lower())+1
        else:
            type2id = dat.index("pokemon_type_none")+1
        msg = "INSERT INTO pokemon VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        arguments = (poki,dexid,form,item[pokemon_name]["stats"]["baseAttack"],
                    item[pokemon_name]["stats"]["baseDefense"],item[pokemon_name]["stats"]["baseStamina"],
                    type1id, type2id, bcr, rarity)
        
        #msg = "INSERT INTO pokemon VALUES(?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)"
        #arguments = (poki,dexid,form,item[pokemon_name]["stats"]["baseAttack"],
        #            item[pokemon_name]["stats"]["baseDefense"],item[pokemon_name]["stats"]["baseStamina"],
        #            type1id, bcr, rarity)
        c.execute(msg,arguments)
        
        
        if "tempEvoOverrides" in item[pokemon_name]:
            megai = 0
            for i in range(len(item[pokemon_name]["tempEvoOverrides"])):
                mega = item[pokemon_name]["tempEvoOverrides"][i]
                if "tempEvoId" not in mega:
                    continue
                #if item[pokemon_name]["pokemonId"].lower()=='aggron':
                #print(list(mega.keys()))
                #if item[pokemon_name]["pokemonId"].lower()=='abomasnow':
                #    print(mega["stats"])
                form = pok_name+'_'+mega["tempEvoId"].lower()[15:]
                type1id = dat.index(mega["typeOverride1"].lower())+1
                if "typeOverride2" in mega:
                    type2id = dat.index(mega["typeOverride2"].lower())+1
                else:
                    type2id = dat.index("pokemon_type_none")+1
                msg = "INSERT INTO pokemon VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                arguments = (poki+megai+1,dexid,form,mega["stats"]["baseAttack"],
                            mega["stats"]["baseDefense"],mega["stats"]["baseStamina"],
                            type1id, type2id, bcr, rarity)
                #else:
                #    msg = "INSERT INTO pokemon VALUES(?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)"
                #    arguments = (poki+megai+1,dexid,form,mega["stats"]["baseAttack"],
                #            mega["stats"]["baseDefense"],mega["stats"]["baseStamina"],
                #            type1id, bcr, rarity)
                c.execute(msg,arguments)
                megai+=1
        
        #special morpeko handling. Keep this until Game master changes
        if pok_name=='morpeko':
            cmove = item[pokemon_name]["cinematicMoves"]
            cmove.remove(406)
            cmove = cmove+['aura_wheel_electric']
            moves = item[pokemon_name]["quickMoves"]+cmove
            moves = set(moves)
            for move in moves:
                ind = movearr.index(move.lower())+1
                for movei in range(megai+1):
                    c.execute("INSERT INTO pk_move VALUES(?,?)",(poki+movei,ind))
        else:
            if "quickMoves" in item[pokemon_name]:
                moves = item[pokemon_name]["quickMoves"]+item[pokemon_name]["cinematicMoves"]
                moves = set(moves)
                for move in moves:
                    ind = movearr.index(move.lower())+1
                    for movei in range(megai+1):
                        c.execute("INSERT INTO pk_move VALUES(?,?)",(poki+movei,ind))
        if "eliteQuickMove" in item[pokemon_name]:
            moves = item[pokemon_name]["eliteQuickMove"]#+item[pokemon_name]["cinematicMoves"]
            moves = set(moves)
            for move in moves:
                ind = movearr.index(move.lower())+1
                for movei in range(megai+1):
                    c.execute("INSERT INTO pk_move VALUES(?,?)",(poki+movei,ind))
        if "eliteCinematicMove" in item[pokemon_name]:
            moves = item[pokemon_name]["eliteCinematicMove"]#+item[pokemon_name]["cinematicMoves"]
            moves = set(moves)
            for move in moves:
                ind = movearr.index(move.lower())+1
                for movei in range(megai+1):
                    c.execute("INSERT INTO pk_move VALUES(?,?)",(poki+movei,ind))
        if form in special_moves:
            ind = movearr.index(special_moves[form])+1
            for movei in range(megai+1):
                c.execute("INSERT INTO pk_move VALUES(?,?)",(poki+movei,ind))
            
        poki+=(1+megai)
        megai = 0
    
    if cup:
        previous_ind = 0
        for file in os.listdir("data/"):
            if file.endswith(".cup"):
                previous_ind = add_cup_from_file(file[:-4],c=c,old_ind=previous_ind,debug=debug)
                print( "    Added %s cup data ..."%(file[:-4]))
     
    conn.commit()
    conn.close()
    
    #with open('data/eff.json', 'w') as outfile:
    #    json.dump(eff, outfile,sort_keys=True, indent=4, separators=(',',':'))
    
    #create related data
    stardusts = np.array([val for val in stardust for _ in (0, 1)][:-1])
    cpmultis = np.array([val for val in cpmulti for _ in (0, 1)][:-1])
    
    for i in range(len(cpmultis)):
        if i%2==1:
            cpmultis[i]=np.sqrt((cpmultis[i]**2+cpmultis[i+1]**2)/2)
    lvl = np.arange(2,max_level*2+1)
    arr = np.zeros(len(lvl), dtype=[('lvl','i4'), ('cpm','f4'),('stardust','i4')])
    arr['lvl'] = lvl
    arr['cpm'] = cpmultis[:len(lvl)]
    arr['stardust'][:len(stardusts)] = stardusts
    np.save('data/cpm.npy',arr)
    
    print( "    Successful!!!")
    
    if not dbno:
        DB.init_database()
    return

def add_cup_from_file(cup, c=None, old_ind=0,debug=False):
    #should update to read in names instead
    if c==None:
        c=DB.__cur__
    ban_sp = None
    ban_type = None
    ban_rare = None
    with open('data/%s.cup'%cup,'r') as f:
        lines = [line.rstrip() for line in f]
        if len(lines)>2:
            ban_sp = lines[2].split(',')
            if ban_sp[0]=='':
                ban_sp = None
        if len(lines)>3:
            ban_type = lines[3].split(',')
            if ban_type[0]=='':
                ban_type = None
            else:
                ban_type = ['pokemon_type_'+x.lower() for x in ban_type]
        if len(lines)>4:
            ban_rare = lines[4].split(',')
        if lines[0]=='dexid':
            string = lines[1].replace(' ','').lower()
            string = string.split(',')
            dexlist = []
            for i in range(len(string)):
                if '-' in string[i]:
                    start, end = string[i].split('-')
                    for j in range(int(start),int(end)+1):
                        dexlist.append(j)
                else:
                    dexlist.append(int(string[i]))
            c.execute("SELECT id, dexid FROM pokemon")
            alist = np.array(c.fetchall()).T
            mask = np.in1d(alist[1],dexlist)
            addlist = alist[0][mask]
            for i in range(len(addlist)):
                c.execute("INSERT INTO cup VALUES(?, ?, ?)",(i+1+old_ind,cup,addlist[i]))
            return len(addlist)+1+old_ind
        elif lines[0]=='type':
            string = lines[1].replace(' ','').lower()
            string = string.split(',')
            ret = build_cup_from_type(cup,string,ban_spec=ban_sp,ban_type=ban_type,ban_rare=ban_rare,c=c,old_ind=old_ind,debug=debug)
            return ret

def build_cup_from_type(cup, types, ban_spec=None, ban_type=None, ban_rare=None, c=None, old_ind=0, debug=False):
    if c==None:
        c=DB.__cur__
    pok_cond = "("
    for i in range(len(types)):
        types[i] = 'pokemon_type_'+types[i].lower()
        pok_cond += "(typ1.name=='%s' OR typ2.name=='%s') "%(types[i],types[i])
        if i!=len(types)-1 :
            pok_cond += "OR"
    pok_cond += ") "
    ban = ban_spec or ban_type or ban_rare
    if ban:
        if ban_spec!=None:
            if isinstance(ban_spec, six.string_types):
                pok_cond += " AND (pokemon.name!='%s' ) "%(ban_spec)
            else:
                for i in range(len(ban_spec)):
                    pok_cond += " AND (pokemon.name!='%s' ) "%(ban_spec[i])
        if ban_type!=None:
            if isinstance(ban_type, six.string_types):
                pok_cond += " AND (typ1.name!='%s' AND typ2.name!='%s') "%(ban_type,ban_type)
            else:
                for i in range(len(ban_type)):
                    pok_cond += " AND (typ1.name!='%s' AND typ2.name!='%s') "%(ban_type[i],ban_type[i])
        if ban_rare!=None:
            if isinstance(ban_rare, six.string_types):
                pok_cond += " AND (pokemon.rarity!='%s') "%(ban_rare)
            else:
                for i in range(len(ban_rare)):
                    pok_cond += " AND (pokemon.rarity!='%s') "%(ban_rare[i])    
    message = '''SELECT pokemon.id, pokemon.name FROM pokemon
    LEFT JOIN type AS typ1 ON pokemon.type1=typ1.id  
    LEFT JOIN type AS typ2 ON pokemon.type2=typ2.id
    WHERE '''+pok_cond
    if debug:
        print(message)
    c.execute(message)
    alist = np.array(c.fetchall()).T
    addlist = alist[0]
    for i in range(len(addlist)):
        c.execute("INSERT INTO cup VALUES(?, ?, ?)",(i+1+old_ind,cup,addlist[i]))
    #with open('data/%s.cup'%cup,'w') as f:
    #    for i in range(len(addlist)):
    #        if alist[2][i]!=None:
    #            f.write(alist[2][i])
    #        else:
    #            f.write(alist[1][i])
    #        if i!=len(addlist)-1:
    #            f.write(',')
    return len(addlist)+1+old_ind
    
if __name__=="__main__":
    if len(sys.argv)>1:
        update_gm(url=sys.argv[1],dbno=True)
    else:
        update_gm(dbno=True)