import numpy as np
from .db import DB
import six


class Move(object):
    def __init__(self,move,pvp=False, sep2024_rounding = 0):
        self.dmg = None
        self.pvp = pvp
        
        if pvp:
            retrieve = '''SELECT move.pvpd,move.pvpe,move.pvpt,type.name
                                    FROM move
                                    LEFT JOIN type ON move.type=type.id WHERE'''
            if isinstance(move, six.string_types):
                DB.__cur__.execute("%s move.name='%s'"%(retrieve,move))
            elif isinstance(move, int):
                DB.__cur__.execute("%s move.id=%d"%(retrieve,move))
            a = DB.__cur__.fetchone()
            self.dmg = a[0]
            self.e = a[1]
            self.t = a[2]
            self.type = a[3]
        else:
            retrieve = '''SELECT move.d,move.e,move.t,type.name
                                    FROM move
                                    LEFT JOIN type ON move.type=type.id WHERE'''
            if isinstance(move, six.string_types):
                DB.__cur__.execute("%s move.name='%s'"%(retrieve,move))
            elif isinstance(move, int):
                DB.__cur__.execute("%s move.id=%d"%(retrieve,move))
            a = DB.__cur__.fetchone()
            self.dmg = a[0]
            self.e = a[1]
            sep2024_update_stage = [0,1,2]
            match sep2024_update_stage[sep2024_rounding]:
                case 0:
                    self.ms = a[2]
                case 1:
                    self.ms = np.round(a[2]*2, -3)/2
                case 2:
                    self.ms = np.round(a[2]*2, -3)/2
                    if np.abs(1- a[2]/self.ms)>0.199:
                        self.dmg =  a[0]*(2- (a[2]/self.ms))
            self.type =a[3]
        if self.dmg==None:
            raise RuntimeError("Move (%s) NOT Found!!!"%move)
        return
    
    def explore(self):
        if self.pvp:
            if self.e>0:
                print( "Dpt: %.1f, Ept: %.1f, Turn: %d, Type: %s"%(self.dmg*1./self.t,self.e*1./self.t,self.t,self.type))
            else:
                print( "Dpe: %.1f, E: %d, Type: %s"%(-self.dmg*1./self.e,-self.e,self.type))
        else:
            if self.e>0:
                print( "Dps: %.1f, Eps: %.1f, Time: %d ms, Type: %s"%(self.dmg*1000./self.ms,self.e*1000./self.ms,self.ms,self.type))
            else:
                print( "Dps: %.1f, Dpe: %.1f, E: %d, Type: %s"%(self.dmg*1000./self.ms,-self.dmg/self.e,-self.e,self.type))
            
            




def learn(move=None, pokemon=None,cup=None,debug=False,pvprank=False):
    """
    Usage: learn(move, **kwargs)
    
    Parameters
    ----------
    move : str or array of str
        str must be move name or pokemon type of move (starting with pokemon_type_).
        To check for more than 1 moves, use array of str
    pokemon : str, optional
        Name of pokemon to check if the move can be learned.
        Default is None, and will check cup.
    cup : str, optional
        Name of Silph cup from which the learners should be searched for.
        Default is None, and will look through all pokemons
    debug : bool, optional
        If True, it will print sql statement to run
        Default is False.
    pvprank : bool, optional
        If True, the pokemon will be ranked by pvp stat product under a cp cap.
        This is useful for great and ultra league. The maximum cp a pokemon can reach is ignored.
        Default is False.
    
    Output
    ----------
    None
        It will print the pokemons that can learn the move specified within the specified limit.
    """

    #if move is not given, print all moves learned by the pokemon
    if move==None:
        if pokemon==None:
            raise ValueError("Either move or pokemon must be specified!!!")
        sql_statement = "SELECT pokemon.name,move.name"+\
                        " FROM pokemon JOIN pk_move ON pokemon.id=pk_move.pk_id "+\
                        "JOIN move ON move.id=pk_move.move_id WHERE pokemon.name=='%s'"%pokemon
        if debug:
            DB.turn_on_statement()
        DB.__cur__.execute(sql_statement)
        alist = np.array(DB.__cur__.fetchall()).T
        if len(alist)<1:
            print( "No Pokemon found ... ")
            return
        uniq = alist[0]
        for i in range(len(uniq)):
            print( alist[1][i])
        print( "    DONE !!!")
        if debug:
            DB.turn_on_statement()
        return 

    #now move is given, look for pokemon that can learn it
    if isinstance(move, six.string_types):
        move = [move.lower().replace(" ","_")]
    else:
        for i in range(len(move)):
            move[i] = move[i].lower().replace(" ","_")
    
    #prepare sql query move conditions to check for
    join = [None]*len(move)
    condition = [None]*len(move)
    pok_type = False
    select_join = ""
    for i in range(len(move)):
        if move[i][:12]=='pokemon_type':
            join[i] = " LEFT JOIN type as typ3 ON move.type=typ3.id"
            condition[i] = "typ3.name=='%s'"%move[i]
            pok_type = True
            select_join = ",move.name"
        else:
            pok_type = False
            join[i] = ""
            condition[i] = "move.name=='%s'"%move[i]
    
    #prepare sql query pokemon to check for
    pok_join = ""
    pok_cond = ""
    if pokemon!=None:
        pokemon = pokemon.lower().replace(" ","_")
        if pokemon[:12]=='pokemon_type':
            pok_join = " LEFT JOIN type AS typ1 ON pokemon.type1=typ1.id "+\
                        " LEFT JOIN type AS typ2 ON pokemon.type2=typ2.id "
            pok_cond = "(typ1.name=='%s' OR typ2.name=='%s') AND "%(pokemon,pokemon)
        else:
            pok_cond = "pokemon.name=='%s' AND "%pokemon
    elif cup!=None:
        #cup option will look through cup table in database. must be preloaded
        pok_join = " LEFT JOIN cup ON pokemon.id=cup.id "
        pok_cond += "(cup.name=='%s') AND "%(cup)
    
    #pvprank
    pvpstat = ""
    pvporder = ""
    if pvprank:
        cpmlist = np.load('data/cpm.npy')
        compare = "%.2f"%(1100**2*100/cpmlist['cpm'][-1]**2)
        pvpstat = ",CAST(pokemon.def as float)*pokemon.sta/(pokemon.atk*pokemon.atk) as stat "
        pvporder = " AND pokemon.atk*pokemon.atk*pokemon.def*pokemon.sta > "+compare+" ORDER BY stat desc"
    
    #general sql statement
    sql_statement = "SELECT pokemon.id,pokemon.name"+select_join+pvpstat+\
                    " FROM pokemon JOIN pk_move ON pokemon.id=pk_move.pk_id "+\
                    "JOIN move ON move.id=pk_move.move_id"
    i=0
    while i<len(move):
        mod = sql_statement+pok_join+join[i]+" WHERE "+pok_cond+condition[i]+pvporder
        if debug:
            DB.turn_on_statement()
        DB.__cur__.execute(mod)
        alist = np.array(DB.__cur__.fetchall()).T
        if len(alist)<1:
            print( "No Pokemon can learn the move/moves ... ")
            return
        if i==0:
            uniq = alist[0]
            ind2 = range(len(uniq))
        else:
            uniq, ind1, ind2 = np.intersect1d(uniq,alist[0],return_indices=True)
        i+=1
        #loop through move, find intersection for each moves

    for i in range(len(uniq)):
        #print form name, or pokemon name
        move_join = ""
        if pok_type:
            move_join = alist[2][ind2[i]]
        print( alist[1][ind2[i]]+" "+move_join)
        
    print( "    DONE !!!")
    if debug:
        DB.turn_on_statement()
    return 
        
def pvp_fast_move_ranking(energy_weight = 1.5, pokemon_type = None, pokemon=None, top_n = None, debug=False):
    """
    Usage: pvp_fast_move_ranking(energy_weight = 1.5)
    
    Parameters
    ----------
    energy_weight : float, optional
        number between 1 and 2. Roughly, this is average damage per energy of the charge move.
        The higher this number is, the more effective the charge moves are (energy is more important).
        Initial silphroad research uses 1.3. Most pvp viable sets will be best with 1.5-1.7. 
        Default is 1.5. 
        Formula for ranking number is dpt + ept*energy_weight.
    pokemon_type: string, optional
        String must start with pokemon_type_. If set, only list moves with these types
        Default is None and will list all moves. 
    pokemon: string, optional
        String, pokemon name. If set, only list moves that this pokemon can learn.
        Will be ignored if pokemon_type is set.
        Default is None and will list all moves. 
    top_n: int, optional
        Only lists top n of fast moves of given condition.
    debug: bool, optional
        If True, will print sql statement used.
        Default is False.
    
    Output
    ----------
    None
        It will print the rankings of pokemon fast move in pvp.
    """
    if pokemon_type is None:
        if pokemon is not None:
            type_table = " JOIN pk_move ON move.id=pk_move.move_id JOIN pokemon ON pokemon.id=pk_move.pk_id "
            type_selection = 'AND pokemon.name==\"%s\"'%(pokemon)
        else:
            type_table = ""
            type_selection = ""
    elif 'pokemon_type' in pokemon_type:
        type_table = " JOIN type ON move.type=type.id " 
        type_selection = 'AND type.name==\"%s\"'%(pokemon_type)
    else:
        raise ValueError("Invalid pokemon_type or pokemon")    
    if top_n is None:
        limit_selection = ""
    else:
         limit_selection = " LIMIT %d"%(top_n)
    
    if debug:
        DB.turn_on_statement()
    fmove = DB.explore("SELECT move.name, move.pvpd, move.pvpe, move.pvpt, "+\
    "(move.pvpd+move.pvpe*%.2f)/move.pvpt AS ranking "%(energy_weight)+\
    "FROM move"+type_table+" WHERE pvpe>0 "+type_selection +\
     "ORDER BY ranking DESC" + limit_selection)

    print('{0: <20} : ranking, damage, energy, turn '.format('Move name') )
    for i in range(len(fmove)):
        print('{0: <20} : {1:.2f} , d={2:2d}, e={3:2d}, t={4:} '.format(fmove[i][0], fmove[i][4], fmove[i][1], fmove[i][2], fmove[i][3]) )
    if debug:
        DB.turn_on_statement()
    return
    
def pvp_charge_move_ranking(energy_weight = 1., pokemon_type = None, pokemon=None, top_n = None, debug=False):
    """
    Usage: pvp_charge_move_ranking(energy_weight = 1, pokemon_type = None, top_n = None)
    
    Parameters
    ----------
    energy_weight : float, optional
        number between 0 and 2. Roughly, this is the average shield remaining.
        The higher this number is, the more likely the charge moves will be shielded (low energy moves are better).
        Initial silphroad research uses 1. Default is also 1. 
        If it is 0, it is ranked purely by damage per energy (most important in no shield scenario).
        Formula for ranking number is dpe * (100/e)**energy_weight
    pokemon_type: string, optional
        String must start with pokemon_type_. If set, only list moves with these types
        Default is None and will list all moves. 
    pokemon: string, optional
        String, pokemon name. If set, only list moves that this pokemon can learn.
        Will be ignored if pokemon_type is set.
        Default is None and will list all moves. 
    top_n: int, optional
        Only lists top n of fast moves of given condition.
    debug: bool, optional
        If True, will print sql statement used.
        Default is False.
    
    Output
    ----------
    None
        It will print the rankings of pokemon charge move in pvp.
    """
    if pokemon_type is None:
        if pokemon is not None:
            type_table = " JOIN pk_move ON move.id=pk_move.move_id JOIN pokemon ON pokemon.id=pk_move.pk_id "
            type_selection = 'AND pokemon.name==\"%s\"'%(pokemon)
        else:
            type_table = ""
            type_selection = ""
    elif 'pokemon_type' in pokemon_type:
        type_table = " JOIN type ON move.type=type.id " 
        type_selection = 'AND type.name==\"%s\"'%(pokemon_type)
    else:
        raise ValueError("Invalid pokemon_type or pokemon")    
    if top_n is None:
        limit_selection = ""
    else:
         limit_selection = " LIMIT %d"%(top_n)
        
    if debug:
        DB.turn_on_statement()
    cmove = DB.explore("SELECT move.name, move.pvpd, move.pvpe, "+\
    "-(CAST(move.pvpd AS float)/move.pvpe)*POWER(100/CAST(-move.pvpe AS float), %.2f) AS ranking "%(energy_weight)+\
    "FROM move"+type_table+" WHERE pvpe<0 "+type_selection +\
     "ORDER BY ranking DESC" + limit_selection)
         
    print('Not taking into account the stat buff/drops.' )
    print('{0: <20} : ranking, damage, energy '.format('Move name') )
    for i in range(len(cmove)):
        print('{0: <20} : {1:.2f} , d={2:3d}, e={3:3d} '.format(cmove[i][0], cmove[i][3], cmove[i][1], -cmove[i][2]) )
    if debug:
        DB.turn_on_statement()
    return  

