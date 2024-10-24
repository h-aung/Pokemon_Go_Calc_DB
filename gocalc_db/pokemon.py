from astropy.table import Table
from .db import DB
from .move import Move
import six
from functools import reduce
import numpy as np
#conversion to db done

class Pokemon(object):
    def __init__(self,pokemon,bstat=None,load_pve=False,load_pvp=False):
        self.batk = None
        retrieve = '''SELECT pkmn.atk,pkmn.def,pkmn.sta,pkmn.bcr,pkmn.id,typ1.name,typ2.name
                        FROM pokemon as pkmn 
                        LEFT JOIN type AS typ1 ON pkmn.type1=typ1.id
                        LEFT JOIN type AS typ2 ON pkmn.type2=typ2.id
                        WHERE '''
        if isinstance(pokemon, six.string_types):
            DB.__cur__.execute("%s pkmn.name='%s'"%(retrieve,pokemon))
        elif isinstance(pokemon, int):
            DB.__cur__.execute("%s pkmn.id=%d"%(retrieve,pokemon))
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
        
        if load_pvp:
            self.fmove = Table(names=('name','dmg', 'e','turn','type'), dtype=('S32','f4', 'f4', 'i4','S32'))
            self.cmove = Table(names=('name','dmg', 'e','type'), dtype=('S32','f4', 'f4', 'S32'))
            DB.__cur__.execute('''SELECT move.name,move.pvpd,move.pvpe,move.pvpt,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e>0''',(a[4],))
            for i in DB.__cur__.fetchall():
                self.fmove.add_row(i)
            DB.__cur__.execute('''SELECT move.name,move.d,move.e,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e<0''',(a[4],))
            for i in DB.__cur__.fetchall():
                self.cmove.add_row(i)
        elif load_pve:
            self.fmove = Table(names=('name','dmg', 'e','t','type'), dtype=('S32','f4', 'f4', 'i4','S32'))
            self.cmove = Table(names=('name','dmg', 'e','t','type'), dtype=('S32','f4', 'f4', 'f4','S32'))
            DB.__cur__.execute('''SELECT move.name,move.d,move.e,move.t,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e>0''',(a[4],))
            for i in DB.__cur__.fetchall():
                self.fmove.add_row(i)
            DB.__cur__.execute('''SELECT move.name,move.d,move.e,move.t,type.name
                                FROM pk_move
                                JOIN move ON move.id=pk_move.move_id
                                LEFT JOIN type ON move.type=type.id
                                WHERE pk_move.pk_id==? AND move.e<0''',(a[4],))
            for i in DB.__cur__.fetchall():
                self.cmove.add_row(i)
        return
        
class CalcIV(object):
    class Decorators(object):
        @classmethod
        def docstring_parameter(self):
            def dec(obj):
                extra = """
        Parameters
        ----------
        pokemon : string
            name of pokemon.
        level : int
            Level of pokemon.
            Default is 20. 
        raid : bool, optional
            True if you are catching a raid boss. Default is False.
            It will override lvl if True. Either raid is True or lvl must be given.
        weather : bool, optional
            True if the pokemon is weather boosted. Default is False.
            It will not work if raid is False.
        number : int, optional
            Number of throws for a pokemon, i.e. if the first throw doesn't catch, 
            it will try a second one and so on, until it is caught or exceeds number of throws.
            Default is 1."""
                obj.__doc__ = obj.__doc__.format(extra)
                return obj
            return dec
        
    def __init__(self,pokemon):
        if isinstance(pokemon,six.string_types):
            retrieve = '''SELECT pkmn.atk,pkmn.def,pkmn.sta
                            FROM pokemon as pkmn WHERE '''
            DB.__cur__.execute("%s pkmn.name='%s'"%(retrieve,pokemon))
            a = DB.__cur__.fetchone()
            self.batk = a[0]
            self.bdef = a[1]
            self.bsta = a[2]
        else:
            self.batk = pokemon.batk
            self.bdef = pokemon.bdef
            self.bsta = pokemon.bsta
        self.cpmlist = np.load('data/cpm.npy')
        return
    
    def atk(self,level,aiv,cpm=None):
        if cpm==None:
            cpm = self.cpmlist['cpm'][level-2]
        return (self.batk+aiv)*cpm
        
    def dfn(self,level,div,cpm=None):
        if cpm==None:
            cpm = self.cpmlist['cpm'][level-2]
        return (self.bdef+div)*cpm
        
    def hp(self,level,siv,cpm=None):
        if cpm==None:
            cpm = self.cpmlist['cpm'][level-2]
        return (self.bsta+siv)*cpm
    
    @Decorators.docstring_parameter()
    def cp(self,level=20,iv=[0,0,0],doubled=False,hp=False,cpm=None):
        """{0}"""
        if not doubled:
            level = int(level*2)
        if hp:
            hpm = self.hp(level,iv[2])
            return np.floor(self.atk(level,iv[0])*np.sqrt(self.dfn(level,iv[1])*hpm)/10.).astype(int), np.floor(hpm)
        else:
            return np.floor(self.atk(level,iv[0])*np.sqrt(self.dfn(level,iv[1])*self.hp(level,iv[2]))/10.).astype(int)
    
    @Decorators.docstring_parameter()
    def pvpcp(self,iv=[0,0,0],league='great',stat=False, max_level=50):
        """
        Usage: cp, stat_product, level = CalcIV.pvpcp(iv,league)
        
        Parameters
        ----------
        iv: [atk, def, hp]
            length 3 array of iv's in integers
        league: string
            name of league to aim for, which will set the max cp
            great, ultra, or master. Default is great.
        
        Output
        ----------
        cp: integer, the highest possible cp
        level: float, level to achieve this cp and stats
        stat_product: optional float, the highest possible stat products (~TDO)
        """
        cpmaxdict = {'great':1500,'ultra':2500,'master':10000}
        if league in cpmaxdict:
            cpmax = cpmaxdict[league]
        else:
            raise ValueError("Given league \(%s\) does not exist!!!"%league)
        level = np.arange(2,max_level*2+1)
        atk = self.atk(level,iv[0])
        dfn = self.dfn(level,iv[1])
        hp = self.hp(level,iv[2])
        cp = np.floor(atk*np.sqrt(dfn*hp)/10.).astype(int)
        mask = cp<=cpmax
        if stat:
            statprod = atk*dfn*np.floor(hp)
            return cp[mask][-1], level[mask][-1]/2., statprod[mask][-1]
        else:
            return cp[mask][-1], level[mask][-1]/2.

    def pvprank(self,league='great',trank = 50, iv = None):
        """{0}"""
        miniv = 0
        maxiv = 15
        total = maxiv-miniv+1
        atkiv = np.repeat(np.arange(miniv,maxiv+1),total*total)
        defiv = np.tile(np.arange(miniv,maxiv+1),total*total)
        staiv = np.zeros(total*total*total,dtype='i4')
        stats = np.zeros(len(atkiv))
        cp = np.zeros(len(atkiv))
        level = np.zeros(len(atkiv))
        for i in range(total):
            for j in range(total):
                staiv[i*total+j*total*total:i*total+j*total*total+total] = i+miniv
        for i in range(len(atkiv)):
            cp[i], level[i], stats[i] = self.pvpcp(iv=[atkiv[i],defiv[i],staiv[i]],league=league,stat=True)
        ind = np.argsort(stats)
        ind = ind[::-1]
        atkiv = atkiv[ind]
        defiv = defiv[ind] 
        staiv = staiv[ind] 
        stats = stats[ind] 
        cp = cp[ind] 
        level = level[ind] 
        stats = stats*100./stats[0]
        print( "    Rank atk def sta cp level stats\n")
        for i in range(trank):
            print( "    %d %.0f %.0f %.0f %.0f %.1f %.2f"%(i+1,atkiv[i],defiv[i],staiv[i],cp[i],level[i],stats[i]))
        if iv is not None:
            aind = np.where(atkiv==iv[0])[0]
            dind = np.where(defiv==iv[1])[0]
            sind = np.where(staiv==iv[2])[0]
            ind = reduce(np.intersect1d, (aind,dind,sind))
            if len(ind)!=1:
                print( "    Given IV is weird!!!")
                return
            print( "    %d %.0f %.0f %.0f %.0f %.1f %.2f"%(ind[0]+1,atkiv[ind[0]],defiv[ind[0]],staiv[ind[0]],cp[ind[0]],level[ind[0]],stats[ind[0]]))
        return
            

    @Decorators.docstring_parameter()
    def iv(self,cp,hp,level=None,stardust=None,raid_catch=False,catch=False,appraisal=None,percent=False,printout=True):
        """
        Usage: iv(, percent) = CalcIV.iv(cp,**kwargs)
        {0}
        appraisal: [percent,max,range]
            percent = 0 for below average(-50), 1 for above average(51-67), 2 for certainly caught(68-80), 3 forwonder(81-)
            max = [0] for atk, 1 for def, 2 for hp. [0,1] for multiple
            range = 0 for 0-7, 1 for 8-12, 2 for 13-14, 3 for 15
        
        Output
        ----------
        iv : array of [atk, def, sta]
            Possible IV of individual stats
        """
        if raid_catch:
            miniv = 10
        else:
            miniv = 0
        maxiv = 15
        total = maxiv-miniv+1
        atkiv = np.repeat(np.arange(miniv,maxiv+1),total*total)
        defiv = np.tile(np.arange(miniv,maxiv+1),total*total)
        staiv = np.zeros(total*total*total,dtype='i4')
        for i in range(total):
            for j in range(total):
                staiv[i*total+j*total*total:i*total+j*total*total+total] = i+miniv
        if level==None:
            if stardust==None:
                raise RuntimeError("You need to specify the level or required stardust to power up.")
            else:
                level = self.cpmlist[self.cpmlist['stardust']==stardust]['lvl']
                if catch:
                    level = level[~(level%2).astype(bool)]
        else: 
            level = int(level*2)
        if not hasattr(level, "__len__"):
            level=[level]
        lvls = np.repeat(level,len(atkiv))
        atkiv = np.tile(atkiv,len(level))
        defiv = np.tile(defiv,len(level))
        staiv = np.tile(staiv,len(level))
        
        cplist, hplist = self.cp(level=lvls,iv=[atkiv,defiv,staiv],doubled=True,hp=True)
        mask = (cplist==cp) & (hplist==hp)
        lvls = lvls[mask]
        atkiv = atkiv[mask]
        defiv = defiv[mask]
        staiv = staiv[mask]
        
        if appraisal!=None:
            if len(appraisal)!=3:
                print( "Wrong appraisal. It won't be used.")
                pass
            else:
                sumlimit = [0,0.51,0.68,0.81]
                sumiv = (atkiv+defiv+staiv)/45.
                summask = sumiv>=sumlimit[appraisal[0]]
                lvls = lvls[summask]
                atkiv = atkiv[summask]
                defiv = defiv[summask]
                staiv = staiv[summask]
        if printout or percent:
            sumiv = (atkiv+defiv+staiv)*100./45
        if printout:
            print( "Possible IV's: \n level atk def hp percent")
            for i in range(len(atkiv)):
                print( " %.1f  %02d  %02d  %02d %.1f%%"%(lvls[i]/2.,atkiv[i],defiv[i],staiv[i],sumiv[i]))
        if percent:
            return [atkiv,defiv,staiv], sumiv
        else:
            return [atkiv,defiv,staiv]
            
class indiPok(Pokemon):
    def __init__(self,pokemon,raid=None,level=None,iv=[15,15,15],fmove=None,cmove=None,pvp=False, sep2024_rounding=0):
        self.shadow = False
        #if form!=None:
        #    if form[-6:]=="shadow":
        #        self.shadow = True
        #if self.shadow:
        Pokemon.__init__(self,pokemon)
        #else:
        #    Pokemon.__init__(self,pokemon,form=form)
        self.pvp = pvp
        
        if raid!=None:
            pok = CalcIV(self)
            raid_tier = [0,20,25,30,40,40]
            level =  int(raid_tier[raid]*2)
            self.atk = pok.atk(level, 15)
            self.dfn = pok.dfn(level, 15)
            self.cp, self.hp = pok.cp(level, [15,15,15], doubled=True, hp=True)
        elif level!=None:
            pok = CalcIV(self)
            if isinstance(level,float):
                level =  int(level*2)
            else:
                level = (level*2).astype('int')
            self.atk = pok.atk(level, iv[0])
            self.dfn = pok.dfn(level, iv[1])
            self.cp, self.hp = pok.cp(level, iv, doubled=True, hp=True)
        if fmove!=None:
            if isinstance(fmove, six.string_types):
                self.fmove = Move(fmove.replace(" ","_")+"_fast",pvp=pvp, sep2024_rounding=sep2024_rounding)
            elif isinstance(fmove, int):
                self.cmove = Move(fmove,pvp=pvp, sep2024_rounding=sep2024_rounding)
            else:
                self.fmove = fmove
        else:
            self.fmove = None
        if cmove!=None:
            if isinstance(cmove, six.string_types):
                self.cmove = Move(cmove.replace(" ","_"),pvp=pvp, sep2024_rounding=sep2024_rounding)
            elif isinstance(cmove, int):
                self.cmove = Move(cmove,pvp=pvp, sep2024_rounding=sep2024_rounding)
            else:
                self.cmove = cmove
        else:
            self.cmove = None
        return
    
    def set_stats(self,level,iv,doubled=False):
        pok = CalcIV(self)
        if not doubled:
            if isinstance(level,int):
                level =  level*2
            elif isinstance(level,float):
                level =  int(level*2)
            else:
                level = (level*2).astype('int')
        self.atk = pok.atk(level, iv[0])
        self.dfn = pok.dfn(level, iv[1])
        self.cp, self.hp = pok.cp(level, iv, doubled=True, hp=True)
        return 