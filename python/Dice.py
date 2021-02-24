import math
import random
import re

# A class based approach to this might be extreme overkill, but is fun to use nevertheless

class Die(object):
    # If we want to allow this to be a hashable type, we would need to make sure that we aren't allowed
    #   to modify self.r or the self.faces data members
    __hash__ = None

    def __init__(self,s,**kwargs):
        '''
            TODO: Create derived classes for the 'special' roll types, such as re-rolling or exploding
                die

            TODO: The method for applying the re-roll condition is really inefficient when the re-roll
                requirement is very high. It would be sufficient to just shift the range of the rolls
                to the min range and then add a corresponding modifier:
                
                    dXrY --> d(X-Y+1)+(Y-1)
                
                This would mean the roll only has to be done exactly once, but will still give the
                exact same distribution.

            See Also: https://wiki.rptools.info/index.php/Dice_Expressions

            Kwargs Description:
                verbose - Sets to verbose output
        '''
        self.sign = 1
        self.r = 0
        self.n = 1
        self.mod = 0
        self.faces = [1,2,3,4,5,6]
        self.__max_face = 6

        v = kwargs.get('verbose',False)
        self._parse(s,verbose=v)

    def _parse(self,s,verbose=False):
        '''
            Description:
                Currently WIP
        '''
        regex_match = re.search(r"(-{0,1})([0-9]*)d{1}([0-9]*)r{0,1}([0-9]*)\+{0,1}([0-9]*)",s)
        if not regex_match:
            raise RuntimeError("Unable to parse string: {}".format(s))
        g1 = regex_match.group(1)
        g2 = regex_match.group(2)
        g3 = regex_match.group(3)
        g4 = regex_match.group(4)
        g5 = regex_match.group(5)

        sign = -1 if g1 else 1
        n    = int(g2) if g2 else 1
        f    = int(g3)
        r    = int(g4) if g4 else 0
        mod  = int(g5) if g5 else 0

        # Make sure that the re-roll is never equal to or larger than the maximum value
        r = min(r,f-1)

        if verbose:
            print "String: {}".format(s)
            print "sign: {}".format(sign)
            print "n: {}".format(n)
            print "f: {}".format(f)
            print "r: {}".format(r)
            print "mod: {}".format(mod)

        self.sign  = sign
        self.n     = n
        self.r     = r
        self.mod   = mod
        self.faces = [x+1 for x in range(f)]

        # Cache this value to avoid repeated lookups
        self.__max_face = max(self.faces)
        # Make sure that the re-roll is never equal to or larger than the maximum value
        self.r = min(self.r,self.__max_face - 1)

        # This is an experimental optimization to avoid having to redo the roll in order to satisfy
        #   the re-roll condition, but still give the exact same distribution. This also means that
        #   the 'while' loop inside of the roll() method should never get executed.
        if self.r > 0:
            self.faces = range(self.r,self.__max_face+1)

    def uid(self):
        '''
            Description:
                This method allows for some type of sensible sorting. The value is based on the n-th
                triangular number + re-roll value
        '''
        x = self.max()
        return x*(x-1)/2 + self.r

    def name(self):
        '''
            Description:
                N/A
        '''
        s = ""
        if self.n > 1:
            s += "{:d}".format(self.n)
        s += "d{:d}".format(self.max())
        if self.r:
            s += "r{:d}".format(self.r)
        if self.mod:
            s += "+{:d}".format(self.mod)
        return s

    def min(self):
        '''
            Description:
                Return the min face value of the die
        '''
        return max(1,self.r)

    def max(self):
        '''
            Description:
                Return the max face value of the die
        '''
        return self.__max_face

    def roll(self):
        '''
            Description:
                Rolls a random value from the list of possible face values on the die
        '''
        total = 0
        for i in range(self.n):
            res = random.choice(self.faces)
            while res < self.r:
                res = random.choice(self.faces)
            total += res*self.sign
        return total + self.sign*self.mod

    def __cmp__(self,other):
        return self.uid().__cmp__(other.uid())

    def __repr__(self):
        return self.name()