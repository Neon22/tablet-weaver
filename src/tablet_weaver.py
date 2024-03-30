# Classes for operating on a tablet weaving loom

# Tasks:
# - Create a configuration.
#   - load and save to this configuration.
#   - Separate loom file to hold config to/from this format.
# - Given an element (cell/sz/card) indicate which targets will be affected by altering this element
#   - and for groups of similar elements
# - Determine the most, and second most, likely action on those targets.


class Tablet_weaver(object):
    """
    A 'Standard' representation of a card loom.
    - variants are dealt with by converting to/from
    - various configurations into this standard format.
    Organised by Card.
    """
    def __init__(self, width, height, cardholes, slants=[]):
        self.holecount = cardholes
        self.width = width
        self.height = height
        self.rpt_length = self.height  # distance to repeat
        self.cards = [Card(i,self.holecount,"S",self.rpt_length) for i in range(self.width)]

    def __repr__(self):
        return f"<Tablets: {self.width}x{self.height}, {self.holecount} hole cards.  Rpt: {self.rpt_length}>"

    def retrieve_targets(self, region="sz", elements=[], modifier=None):
        """
        Given elements (of same type):
        - return list of {element: targets}
        - where targets are list of x,y cells
        """
        targets = {}
        shft,ctrl = modifier
        print('retrieve:',region,elements,modifier)
        if region == "sz":
            if not ctrl:
                # regular click = preserve visual pattern if poss
                for el in elements:
                    x = el[0]
                    if "cells" in targets:
                        targets["cells"].append([x]) #! how to describe rect for whole cell height
                    else:  # no entry yet
                        targets["cells"]= [[x]]
            else:  # modifier on
                pass
        elif region == "cards":
            if not ctrl:
                # regular click = preserve visual pattern if poss
                for el in elements:
                    if "cells" in targets:
                        targets["cells"].append([el[0],el[1]])
                    else:  # no entry yet
                        targets["cells"]= [[el[0],el[1]]]
        #
        return targets
        

class Card(object):
    """
    A card, its parameters, and rpt column
    """
    # Turns are: Fwd,Bwd,Double,Half,Zero(Skip)
    dirs = ['F','B','D','S','H']
    
    def __init__(self, id, holes, slant, length):
        self.id = id
        self.colors = [[]*holes]
        self.slant = slant  # in thread angle
        self.rows = []
        self.switches = []  # the row a switch occurs on and vector. E.g. [3,-2]
        
    def __repr__(self):
        colcount = sum([1 for c in self.colors if c])
        return f"<Card {self.id}: {self.slant}, {colcount} colors, {len(self.switches)} switches>"

    def get_targets(self, eltype, elindices=[]):
        """
        Given a list of elements:
        - return potentially affected targets
        """
        result = []
        if eltype == 'card':
            # only cells can be affected
            result.append({"cells", [2]})
        elif eltype == 'slant':
            # is it only cells
            result.append({"cells", [2]})
        else:  # cells
            # can affect slant and colors
            result.append({"colors", [2]},{"slant": [0]})
        #
        return result

if __name__ == "__main__":
    tab = Tablet_weaver(20,8,4)
    print(tab)
    c1 = tab.cards[0]
    print(c1)

# Notes:
# - Cards CW viewed right = CCW viewed left
# - 




    
# https://youtu.be/7l-FgTEpU7U?t=374
# - CW cards - viewed from left. cardlabels=ABCD from bottom.
#            - start at A,b on top with B close to weaver
#            - Appears in draft as ABCD order
# - flipping cards on border means same direction but cards going B instead of False
# list here: https://www.youtube.com/watch?v=BDEsLOXxLxA&ab_channel=ImpendingLooms
# Twisted threads:
# - Card=ABCD CW - seen from left. Starts A. Fwd is A->B fwp
# - ABCD B2T. SZ shape is tablet angle. color blob is card angle.
# - Draft: (slanted ovals in same dir as tablet slant)
#   - First rows of draft = ABCD. turn = Repeated color, opp angle
#   - Fwd turn has White BG. Bwd is Black BG
#   - Cards numbered L2R
# TDD: (Tablte weaving draft designer)
# - Card=ABCD CW - seen from right. Starts D. Fwd is D->C fwp
# - ABCD T2B. SZ is threading angle. color blob is card angle.
# - Draft: (but slanted ovals in same dir as tablet slant)
#   - First rows of draft = DCBA. turn = Repeated col, opp angle
#   - Fwd turn has White BG. Bwd is Black BG
#   - Cards numbered L2R
# GTT: (Guntram's weaving Thingy)
# - Card=ABCD CW - seen from right. Starts D. Fwd is D->C fwp
# - ABCD T2B. SZ is threading angle. Color blob - no angle
# - Draft: (but slanted diamonds in same dir as tablet slant)
#   - First rows of draft = DCBA. 
#   - Cards numbered L2R
#   - sep yellow turn list
# Book variant 1:
# - ABCD starts D. on right. D->C
# - ABCD is B2T. but pattern starts at ADCBA...
# Book variant 2:
# - Card=ABCD CCW - seen from right. Starts A. Fwd is A->B fwp
# - ABCD T2B. SZ is card angle. color blob is card angle.
# - Draft:
#   - Fwd turn has White BG. Bwd is Black BG
#   - an ellipse inside ellipse shows a Double turn (each ellipse shows color. inner is result)
# hibernaatio.blogspot.com
# - Card=ABCD CCW - seen from right. Starts A. Fwd is A->B fwp
# - SHows cards in perspective with colored holes - good for threading unambiguously (angle slant = card slant)
# - ABCD B2T. SZ is card angle. color blob is card angle.
# - Draft:
#   - First rows of draft = ABCD. 
#   - arrows instead of FB. red line at rpt
# web tiny image swatches
# - ABCD CW facing right. Start DCBA
# Russian web pattern
# - Card=ABCD CW - seen from right. Starts A. Fwd is A->B fwp (Clockwise arrowed circle for dir on card)
# - arrows for slant rather than /
# - rendering examples for band.

# one missing cord, double weave fbfb = spiral round cord
# - https://www.youtube.com/watch?v=ctJHw7gZZKA&ab_channel=DurhamWeaver
# tubular selvedge - three cards. when entering from same side - go under the three with weft
#