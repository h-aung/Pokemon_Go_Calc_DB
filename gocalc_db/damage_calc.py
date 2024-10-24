import numpy as np
from .db import DB
from .pokemon import indiPok
import six

def deffective(move, pokemon):
    """
    Usage: multiple = deffective(move, pokemon)
    
    Parameters
    ----------
    move : string
        POKEMON_TYPE_(*type of move*)
    pokemon : string, or array of string
        string should be POKEMON_TYPE_(*type of pokemon*). For dual types, [str, str].
        string can also be 'None' for neutral damage
    
    Output
    ----------
    multiplier : float
        type effectiveness damage multiplier 
    """
    if pokemon=='None':
        return 1.0
    elif len(pokemon)==1:
        pokemon = pokemon[0]
    else:
        pass
    if isinstance(pokemon,six.string_types): #string, only one type
        DB.__cur__.execute('''select eff.eff
                    FROM eff
                    JOIN type ON type.id=eff.atk
                    LEFT JOIN type AS typ2 ON typ2.id=eff.def
                    WHERE type.name==? AND typ2.name=?
                    ''',(move,pokemon))
        multi = DB.__cur__.fetchone()[0]
    else:
        DB.__cur__.execute('''select eff.eff
                    FROM eff
                    JOIN type ON type.id=eff.atk
                    LEFT JOIN type AS typ2 ON typ2.id=eff.def
                    WHERE type.name==? AND (typ2.name=? OR typ2.name=?)
                    ''',(move,pokemon[0],pokemon[1]))
        multi = np.prod(DB.__cur__.fetchall())
    return multi
    
def damage(pok1,pok2,weather=False,friend=0,rounded=True,option='both',pvp=False,shield=False,debug=False,megastab=False,mega=False):
    """
    Usage: damage = damage(pok1, pok2, **kwargs)
    
    Parameters
    ----------
    pok1 : indiPok
        indiPok of attacker
    pok2 : indiPok
        indiPok of defender
    weather : bool, optional
        weather is boosting the attack or not. Default is False
    friend : int, optional
        friendship status. 0 for None, 1 for Good, 2 for Great, 
        3 for Ultra, 4 for Best. Default is 0.
    rounded: bool, optional
        If True, the damage will be floored + 1. Default is True
    option: str
        Allowed option: both, fmove, cmove
    pvp: bool, optional
        If True, PvP damage is calculated instead. Disables weather and friend boost
    
    Output
    ----------
    damage : (float, float)
        damage dealt by (fast, charge) move
    """
    atk = pok1.atk
    dfn = pok2.dfn
    friendmulti = [1.0,1.03,1.05,1.07,1.1]
    multi = friendmulti[friend] #friend boost
    if weather: #weather boost
        multi*=1.2
    if pvp: #if pvp, ignore friend and weather
        if shield:
            return 1
        multi=1.3
    
    if pok1.shadow:
        multi*=1.2
    if pok2.shadow:
        multi*=1.2
    
    if megastab:
        multi*=1.3
    elif mega:
        multi*=1.1
    #if array_option:
    #    multi = np.ones(len(atk))*multi
        
    if option=='fmove' or option=='both':
        fmulti = deffective(pok1.fmove.type,pok2.type) #effective
        if pok1.fmove.type in pok1.type: #stab attack
            fmulti*=1.2
        fdmg = 0.5*pok1.fmove.dmg*atk*multi*fmulti/dfn
        if debug:
            print( pok1.fmove.dmg, atk, multi, fmulti, dfn, fdmg)
    if option=='cmove' or option=='both':
        cmulti = deffective(pok1.fmove.type,pok2.type) #effective
        if pok1.fmove.type in pok1.type: #stab attack
            cmulti*=1.2
        cdmg = 0.5*pok1.cmove.dmg*atk*multi*cmulti/dfn
    if option=='fmove':
        dmg = fdmg
    elif option=='cmove':
        dmg = cdmg
    elif option=='both':
        dmg = np.array([fdmg, cdmg])
    if rounded:
        return np.floor(dmg)+1
    else:
        return dmg
        
def dps(pok1,pok2,weather=False,friend=0,rounded=True,nocharge=False,timelimit=None):
    """
    Usage: damage = damage(pok1, pok2, **kwargs)
    
    Parameters
    ----------
    pok1 : indiPok
        indiPok of attacker, pvp option must be False.
    pok2 : indiPok
        indiPok of defender, pvp option must be False.
    weather : bool, optional
        weather is boosting the attack or not. Default is False
    friend : int, optional
        friendship status. 0 for None, 1 for Good, 2 for Great, 
        3 for Ultra, 4 for Best. Default is 0.
    rounded: bool, optional
        If True, the damage will be floored + 1. Default is True
    nocharge: bool, optional
        If True, only fast move dps is calculated. Default is False
    timelimit: float, optional
        Default is None. It will average over 100 fast and charge moves combined to represent a better average.
        Float should be in millisecond, can be chosen over some time less than raid times
        to produce more accurate results. timelimit should be chosen to compare more realistic 
        dps between 1 bar and 2/3 bar charge moves.
    
    Output
    ----------
    damage : float
        average damage dealt per second
    """
    if pok1.pvp or pok2.pvp:
        raise RuntimeError("DPS of pokemons in PvP is not supported.")
    fdmg, cdmg = damage(pok1,pok2,weather,friend,rounded)
    ce = np.abs(pok1.cmove.e)

    tdmg = 0
    te = 0
    ttime = 0.
    i=0
    while True:
        tdmg += fdmg
        te += pok1.fmove.e
        ttime += pok1.fmove.ms
        if nocharge:
            pass
        elif te>ce:
            tdmg += cdmg
            te -= ce
            ttime += pok1.cmove.ms
        if timelimit!=None:
            if ttime>timelimit:
                break
        else:
            i+=1
            if i>100:
                break
    return tdmg*1000/ttime
    
def weak_to(move_type, return_id = False, order_by=None, double_weak=False, go_next=False, ignore_eternamax=False, debug=False):
    """
    Usage: list = weak_to(move_type, return_id = False, order_by=None, double_weak=False)
    
    Parameters
    ----------
    move : string
        POKEMON_TYPE_(*type of move*) or just 'type of move'
    return_id : bool
        If true, return ID in database.
        Default is False and return pokemon name.
    order_by: string
        The property to sort the pokemon. Available: atk, sta, def, bcr, cp, stat
        Default is None and sorted by database id. 
    double_weak: bool
        If True, only select pokemon double weak to the move. 
        Default is False.
    go_next: bool
        If True, only used if there is no pokemon with given criteria. 
        Then it will search for pokemon single weak. If None, it will search for neutral.
        Default is False.
    ignore_eternamax: bool
        If True, will remove eternatus eternamax from list. 
        Default is False.
    debug: bool
        If True, will print the sql statement.
        Default is False.
    
    Output
    ----------
    pokemon id in database or pokemon name double weak to the pokemon type.
    """
    if 'pokemon' not in move_type:
        move_type = 'pokemon_type_'+move_type.lower()
        
    if order_by is not None:
        if order_by in ['atk', 'sta', 'def', 'bcr']:
            order_text = ' ORDER BY pokemon.'+ order_by+', pokemon.id'
        elif order_by=='stat':
            order_text = ' ORDER BY pokemon.atk*pokemon.sta*pokemon.def, pokemon.id'
        elif order_by=='cp':
            order_text = ' ORDER BY pokemon.atk*pokemon.atk*pokemon.sta*pokemon.def, pokemon.id'
        else:
            raise ValueError("Cannot order by "+order_by)
    else:
        order_text = ' ORDER BY pokemon.id'
        
    if ignore_eternamax:
        order_text = ' AND pokemon.name!="eternatus_eternamax"'+order_text
        
    if debug:
        DB.turn_on_statement()
        
    select_statement = '''SELECT pokemon.name, pokemon.id, eff1.eff*eff2.eff FROM pokemon 
    JOIN eff AS eff1 ON eff1.def=pokemon.type1
    JOIN eff AS eff2 ON eff2.def=pokemon.type2
    JOIN type ON type.id=eff1.atk 
    WHERE type.name==? AND eff1.atk=eff2.atk'''
    
    cut_off = [0.9, 1.5, 2]
    if double_weak:
        cut_off_ind = 2
    else:
        cut_off_ind = 1
    cutoff_statement = " AND eff1.eff*eff2.eff>%.1f"%(cut_off[cut_off_ind])
    
    DB.__cur__.execute(select_statement + cutoff_statement + order_text, (move_type,))
    test =  DB.__cur__.fetchall()
    
    if go_next:
        i = 1
        while True:
            if len(test)==0:
                cutoff_statement = " AND eff1.eff*eff2.eff>%.1f"%(cut_off[cut_off_ind-i])
                DB.__cur__.execute(select_statement + cutoff_statement + order_text, (move_type,))
                test =  DB.__cur__.fetchall()
                i+=1
            else:
                break
    
    pok_name = np.array([a[0] for a in test])
    pok_id = np.array([a[1] for a in test])
    eff = np.array([a[2] for a in test])
        
    if debug:
        DB.turn_on_statement()
    if return_id:
        return pok_id, eff
    else:
        return pok_name, eff
    
class BreakPoint(object):
    def __init__(self,pokemon1,fmove1,pokemon2,level2, pvp=False):
        """
        Parameters
        ----------
        pokemon1, pokemon2: name of attackers and defenders
        fmove1 : name of fast move from attackers
        level2 : level of defenders (int) or raid tier (str, e.g. '1','2',etc.)
        """
        self.pvp = pvp
        self.pok1 = indiPok(pokemon1,fmove=fmove1, pvp=pvp)
        if self.pok1.fmove.e<0:
            raise RuntimeError("Fast Move not working!!!")
        self.pok2 = indiPok(pokemon2, pvp=pvp)
        if isinstance(level2,six.string_types):
            raid_tier = [0,20,25,30,40,40]
            self.pok2.set_stats(raid_tier[int(level2)],[15,15,15])
        else:
            self.pok2.set_stats(level2,[15,15,15])
    
    def bp(self,iv=15,weather=False,friend=0,debug=False, max_level=51, min_level=20):
        level = np.arange(min_level*2,max_level*2+1)
        self.pok1.set_stats(level,[iv,0,0],doubled=True)
        dmg = damage(self.pok1,self.pok2,weather=weather,friend=friend,option='fmove',pvp=self.pvp,debug=debug)
        #dmg = self.damage(level,iv,doubled=True,weather=weather,friend=friend)
        dmg_inc = dmg[1:]-dmg[:-1]
        ind = np.where(dmg_inc==1)[0]
        if len(ind)==0:
            print( "NO breakpoints!!!")
            print( "Damage = %.0f"%(dmg[0]))
        else:
            print( "The breakpoints are at level and damage:")
            for i in range(len(ind)):
                print( "    At %.1f, dmg=%.0f to at %.1f, dmg=%.0f"%(level[ind[i]]/2.,dmg[ind[i]],level[ind[i]+1]/2.,dmg[ind[i]+1]))
        return