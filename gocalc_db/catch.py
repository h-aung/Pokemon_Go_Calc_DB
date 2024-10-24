import numpy as np
from .pokemon import Pokemon
#no conversion needed

class Catch(object):
    class Decorators(object):
        @classmethod
        def docstring_parameter(self):
            def dec(obj):
                extra = """
        Parameters
        ----------
        curve : bool, optional
            True for curve ball. Default is False.
        ball : string, optional
            Name of the poke balls used. Acceptable lists:
            premier, poke, normal, great, ultra. Default is premier
        throw : string, optional
            Name of throws acheived. Acceptable lists:
            nice, great, excellent, none. Default is none.
        medal1 : string, optional
            Name of medals achieved for the first/only type of pokemon.
            Acceptable lists: bronze, silver, gold, none. Default is none.
        medal2 : string, optional
            Name of medals achieved for the second type of pokemon.
            Acceptable lists: bronze, silver, gold. Default is none.
            medal2 keyword will not work if medal1 is not given.
            If pokemon has only 1 type, use medal1.
        lvl : int, optional
            Level of pokemon trying to catch. It will be overridden if raid is True.
            Default is none. Either raid is True or lvl must be given.
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
        
    def __init__(self,bcr=0,pokemon=None,catch_candies=3,count_xl = None):
        if pokemon==None:
            self.bcr = bcr
        else:
            
            self.bcr = Pokemon(pokemon).bcr
        self.ball = {'premier':1.0, 'great':1.5, 'ultra':2.0}
        self.curve = 1.7
        self.berry = {'razz':1.5, 'golden':2.5, 'pinap':1.0, 'nanab':1.0, 'silver':1.8, 'none':1.0}
        self.throw = {'nice':1.3, 'great':1.5, 'excellent':1.7, 'extreme':1.9, 'none':1.0}
        self.medal = {'bronze':1.1, 'silver':1.2, 'gold':1.3, 'none':1.0, 'platinum':1.4}
        if count_xl is None:
            self.candy = {'razz':catch_candies, 'golden':catch_candies, 'pinap':catch_candies*2, \
                        'nanab':catch_candies, 'silver':int(catch_candies*2.334), 'none':catch_candies}
        else:
            self.candy = {'razz':catch_candies+31, 'golden':catch_candies+31, 'pinap':catch_candies*2+31, \
                        'nanab':catch_candies+31, 'silver':int(catch_candies*2.334)+31, 'none':catch_candies+31}
        self.cpmlist = np.load('data/cpm.npy')
        return
        
    @Decorators.docstring_parameter()
    def catch_prob(self,**kwargs):
        """
        Usage: catch_chance = catch_prob(**kwargs)
        {0}
        berry : string, optional
            Name of berries used. Acceptable lists:
            razz, golden, pinap, nanab, silver, none. Default is none.
        
        
        Output
        ----------
        chance : float
            Chance of catching a pokemon with given conditions
        """
        multiple = 1.0
        
        if 'ball' in kwargs.keys():
            if kwargs['ball']=='normal' or kwargs['ball']=='poke':
                kwargs['ball'] = 'premier'
            multiple *= self.ball[kwargs['ball']]
        
        if 'curve' in kwargs.keys():
            if kwargs['curve']:
                multiple *= self.curve
                
        if 'berry' in kwargs.keys():
            multiple *= self.berry[kwargs['berry']]
            
        if 'throw' in kwargs.keys():
            multiple *= self.throw[kwargs['throw']]
            
        if 'medal1' in kwargs.keys():
            if 'medal2' in kwargs.keys():
                multiple *= (self.medal[kwargs['medal1']]+self.medal[kwargs['medal2']])/2
            else:
                multiple *= self.medal[kwargs['medal1']]
        
        lvl = None
        if 'lvl' in kwargs.keys():
            lvl = int(kwargs['lvl']*2)
        if 'raid' in kwargs.keys():
            if kwargs['raid']:
                lvl = 40
                if 'weather' in kwargs.keys():
                    if kwargs['weather']:
                        lvl = 50
        if lvl==None:
            raise RuntimeError("You need to indicate whether it is a raid or "
                               "specifies a pokemon level.")
        cpm = self.cpmlist[self.cpmlist['lvl']==lvl]['cpm'][0]
    
        chance = 1-(1-self.bcr/(2*cpm))**multiple
        if 'number' in kwargs.keys():
            chance = 1-(1-chance)**kwargs['number'] #1-(1-x)^n
        return chance
    
    @Decorators.docstring_parameter()
    def pinap_candies(self,transfer=True,**kwargs):
        """
        Usage: candies = pinap_candies(**kwargs)
        {0}
        
        Output
        ----------
        candies : float
            Average number of candies given the conditions
        """
        if transfer:
            return self.catch_prob(berry='pinap',**kwargs)*(self.candy['pinap']+1)
        else:
            return self.catch_prob(berry='pinap',**kwargs)*self.candy['pinap']
    
    @Decorators.docstring_parameter()
    def golden_candies(self,transfer=True,**kwargs):
        """
        Usage: candies = golden_candies(**kwargs)
        {0}
        
        Output
        ----------
        candies : float
            Average number of candies given the conditions
        """
        if transfer:
            return catch_prob(berry='golden',**kwargs)*(self.candy['golden']+1)
        else:
            return catch_prob(berry='golden',**kwargs)*self.candy['golden']
    
    @Decorators.docstring_parameter()
    def pinap_other_candies(self,number=1,pinap_number=0,transfer=True,other='golden',chances=False,order='pinap',**kwargs):
        """
        Usage: [catch_chance,] candies = pinap_other_candies(**kwargs)
        {0}
        pinap_number : int or numpy int array, optional
            Number of throws for a pokemon that will be made with pinap berries.
            If not caught, the rest of the throws will be made with other berries or vice versa.
            Check order keyword.
            Default is 0.
        order : string, optional
            Name the berries that will be first used. pinap, other.
            Default is pinap.
        other : string, optional
            Name of second berries used. Acceptable lists:
            razz, golden, pinap, silver, nanab, none. Default is golden.
        chances : bool, optional
            If True, the function will return the probability for the pokemon to be caught.
            Default is False.
        transfer : bool, optional
            True if this pokemon will be transferred for 1 candy. Default is True.
        
        Output
        ----------
        candies : float
            Average number of candies given the conditions
        catch_chance : optional, float
            Chance of catching a pokemon with given conditions
        """
        if hasattr(pinap_number, "__len__"):
            if (number<pinap_number).any():
                raise ValueError("Total number of balls must be equal or less than number of pinap's used.")
        elif (number<pinap_number):
            raise ValueError("Total number of balls must be equal or less than number of pinap's used.")
        chance={'pinap':0.0,'other':0.0,'silver':0.0}
        chance['pinap'] = self.catch_prob(number=pinap_number,berry='pinap',**kwargs)
        chance['other'] = self.catch_prob(number=number-pinap_number,berry=other,**kwargs)
        chance['silver'] = self.catch_prob(number=number-pinap_number,berry=other,**kwargs)
        candies={'pinap':6,'other':3, 'silver':6}
        if order=='pinap':
            tag=['pinap','other']
        else:
            tag=['other','pinap']
        if other=='silver':
            ind = tag.index('other')
            tag[ind] = 'silver'
        if transfer:
            for k in candies:
                candies[k] +=1
        return_candies=chance[tag[0]]*candies[tag[0]] + (1-chance[tag[0]])*chance[tag[1]]*candies[tag[1]]
        if chances:
            return (chance[tag[0]] + (1-chance[tag[0]])*chance[tag[1]]),return_candies
        else:
            return return_candies
            
    
    @Decorators.docstring_parameter()
    def combine_candies(self,number=1,first_number=0,transfer=True,first='pinap',second='golden',chances=False,**kwargs):
        """
        Usage: [catch_chance,] candies = pinap_other_candies(**kwargs)
        {0}
        first_number : int or numpy int array, optional
            Number of throws for a pokemon that will be made with first berry.
            If not caught, the rest of the throws will be made with second berry.
            Default is 0.
        first : string, optional
            Name the berries that will be first used. Acceptable lists:
            razz, golden, pinap, silver, nanab, none. Default is pinap.
        second : string, optional
            Name of second berries used. Acceptable lists:
            razz, golden, pinap, silver, nanab, none. Default is golden.
        chances : bool, optional
            If True, the function will return the probability for the pokemon to be caught.
            Default is False.
        transfer : bool, optional
            True if this pokemon will be transferred for 1 candy. Default is True.
        
        Output
        ----------
        candies : float
            Average number of candies given the conditions
        catch_chance : optional, float
            Chance of catching a pokemon with given conditions
        """
        if hasattr(first_number, "__len__"):
            if (number<first_number).any():
                raise ValueError("Total number of balls must be equal or less than number of first berries used.")
        elif (number<first_number):
            raise ValueError("Total number of balls must be equal or less than number of first berries used.")
        chance=[0.0,0.0]
        chance[0] = self.catch_prob(number=first_number,berry=first,**kwargs)
        chance[1] = self.catch_prob(number=number-first_number,berry=second,**kwargs)
        candies=[0.0,0.0]
        candies[0] = self.candy[first]
        candies[1] = self.candy[second]
        if transfer:
            for k in range(2):
                candies[k] +=1
        return_candies=chance[0]*candies[0] + (1-chance[0])*chance[1]*candies[1]
        if chances:
            return (chance[0] + (1-chance[0])*chance[1]),return_candies
        else:
            return return_candies