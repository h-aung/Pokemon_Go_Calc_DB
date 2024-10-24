import numpy as np
from .pokemon import Pokemon
from .move import Move
from .db import DB
import six
from functools import reduce
#conversion to db done


        
        
class newPokemon(object):
    def __init__(self,pokemon,level,iv,form=None,pvp=False):
        self.shadow = False
        if form!=None:
            if form[-6:]=="shadow":
                self.shadow = True
                
        self.batk = None
        retrieve = '''SELECT pkmn.atk,pkmn.def,pkmn.sta,pkmn.bcr,pkmn.id,typ1.name,typ2.name
                        FROM pokemon as pkmn 
                        LEFT JOIN type AS typ1 ON pkmn.type1=typ1.id
                        LEFT JOIN type AS typ2 ON pkmn.type2=typ2.id
                        WHERE '''
        if form==None:
            DB.__cur__.execute("%s pkmn.name='%s'"%(retrieve,pokemon))
            a = DB.__cur__.fetchone()
        else:
            DB.__cur__.execute("%s pkmn.name='%s' and pkmn.form= '%s'"%(retrieve,pokemon,form))
            a = DB.__cur__.fetchone()
        if a is None:
            raise RuntimeError("Specified pokemon: %s can't be found."%(pokemon))
        if bstat==None:
            self.batk = a[0]
            self.bdef = a[1]
            self.bsta = a[2]
        else:
            self.batk = bstat[0]
            self.bdef = bstat[1]
            self.bsta = bstat[2]
        self.bcr = a[3]
        if a[6]==None:
            self.type = [a[5]]
        else:
            self.type = [a[5],a[6]]
        
        pok = CalcIV(self)
        if isinstance(level,float):
            level =  int(level*2)
        else:
            level = (level*2).astype('int')
        self.atk = pok.atk(level, iv[0])
        self.dfn = pok.dfn(level, iv[1])
        self.cp, self.hp = pok.cp(level, iv, doubled=True, hp=True)
        
        self.pvp = pvp
        if pvp:
            self.fmove = Table(names=('name','dmg', 'e','turn','type'), dtype=('S32','f4', 'f4', 'i4','S32'))
            self.cmove = Table(names=('name','dmg', 'e','type'), dtype=('S32','f4', 'f4', 'S32'))
            DB.__cur__.execute('''SELECT move.name FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e>0''',(a[4],))
            res = DB.__cur__.fetchall()
            self.fmove = [None]*len(res)
            for i in range(len(res)):
                self.fmove[i] = Move(res[i][0], pvp=True)
            DB.__cur__.execute('''SELECT move.name FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e<0''',(a[4],))
            res = DB.__cur__.fetchall()
            self.cmove = [None]*len(res)
            for i in range(len(res)):
                self.cmove[i] = Move(res[i][0], pvp=True)
        else:
            self.fmove = Table(names=('name','dmg', 'e','t','type'), dtype=('S32','f4', 'f4', 'i4','S32'))
            self.cmove = Table(names=('name','dmg', 'e','t','type'), dtype=('S32','f4', 'f4', 'f4','S32'))
            DB.__cur__.execute('''SELECT move.name,move.d,move.e,move.t,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e>0''',(a[4],))
            res = DB.__cur__.fetchall()
            self.fmove = [None]*len(res)
            for i in range(len(res)):
                self.fmove[i] = Move(res[i][0], pvp=False)
            DB.__cur__.execute('''SELECT move.name,move.d,move.e,move.t,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e<0''',(a[4],))
            res = DB.__cur__.fetchall()
            self.cmove = [None]*len(res)
            for i in range(len(res)):
                self.cmove[i] = Move(res[i][0], pvp=False)
        
        if fmove!=None:
            if isinstance(fmove, six.string_types):
                self.fmove = Move(fmove.replace(" ","_")+"_fast",pvp=pvp)
            else:
                self.fmove = fmove
        else:
            self.fmove = None
        if cmove!=None:
            if isinstance(cmove, six.string_types):
                self.cmove = Move(cmove.replace(" ","_"),pvp=pvp)
            else:
                self.cmove = cmove
        else:
            self.cmove = None
        return