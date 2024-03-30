import ltk
import svg as SVG
from math import cos, degrees

g_diamond_ratio = cos(degrees(60))  # y = ax + b  (1.506)


# Need classes for various layers of SVG
# - Draft_BG:
#     - no mouse components. BG only. sizing drawn from here.
#     - special 'handle' resizes entire dimensions
#     - returns its dimensions once drawn for subsequent element repos
# - Pattern - contains F,W and draws user edited values.
# - Draft_ui_layer - mouse sensitive cells over Draft_BG, highlighting, targets
# - Regions - svg sliders for ranges. Text input is separate?
# - Slants - S/Z, slant tools
# - Cards - Region for cards, colors, cardtools

# STYLES
highlight_color = "#E565"
highlight_stroke = "#fffc4c66"
target_s_color = "#4f45"
current_color = "#FF9999"
button_color = "#ffe1b5"
g_brdr2 = 2  # 2px border for offsetting position of other elements
g_brdr1 = 1  # 1px border for offsetting position of other elements
g_brdr05 = 0.5  # 0.5px border for offsetting position of other elements
style = {"fill":"#0C05", "stroke":current_color, "stroke-width": "0.5px"}
diamond_style = {"fill":current_color, "stroke":"#aaa",  "stroke-width":f"{g_brdr05}px"}
highlight_style = {"fill":highlight_color, "stroke":button_color,  "stroke-width":f"{g_brdr2}px"}
target_style = {"fill":"none", "stroke":target_s_color, "stroke-width":f"{g_brdr2}px"}
unseen_style = {"fill":"#00C5", "stroke":"#000", "stroke-width":"0.5px", "opacity": "0"}
border_style = {"fill":"none", "stroke":"#000", "stroke-width":f"{g_brdr2}px"}
sz_style = {"fill":"none", "stroke":"#000", "stroke-width":f"{g_brdr1}px"}
grid_style = {"fill":"none", "stroke":"#aaa", "stroke-width":f"{g_brdr05}px"}
red_tick_style = {"fill":"none", "stroke":"#e00", "stroke-width":f"{g_brdr05}px"}
label_style = {"fill":"#000", "class":"unselectable"}
handle_box_style = {"fill":"#EEE5", "stroke":"#000", "stroke-width":f"{g_brdr2}px"}
handle_line_style = {"fill":"none", "stroke":"#999", "stroke-width":"1px", "class":"ignored"}
button_style = {"fill":button_color, "stroke":"#aaa", "stroke-width":f"{g_brdr05}px"}
#

class Draft_BG(object):
    """ 
    The Draft Background:
    - guide diagonals and row,col markers.
    all encapsulated in the SVG in self.drawing
    """
    def __init__(self, position, dimensions, full_size, size, holecount, loom_prefs):
        self.start = position
        self.size = size  # num_cards, num_steps to draw
        self.dimensions = dimensions  # draft area
        self.holecount = holecount
        self.loom_prefs = loom_prefs
        self.parts_height = 20
        self.parts_gap = 20
        self.sz_gap = 8
        self.cards_gap = 8
        #
        self.cell_width = self.dimensions[0]/(self.size[0])
        self.cell_height = 1/g_diamond_ratio * self.cell_width
        #print("cell width:", self.cell_width, self.cell_height)
        # determine font-size = 3/4 of cell_height or 14pt
        self.label_font_size = min(14, int(self.cell_height*0.8))
        # set manually for the font chosen
        self.label_font_width = self.label_font_size * 0.5
        #print("font-size",self.label_font_size,self.label_font_width)
        #
        self.drawing = SVG.svg(width=full_size[0], height=full_size[1],
                     preserveAspectRatio="xMidYMid meet",
                     viewBox=f"0 0 {full_size[0]} {full_size[1]}")
        self.BG = SVG.g(id="BG")
        # grid
        for item in self.draw_grid():
            self.BG.appendChild(item)
        self.drawing.appendChild(self.BG)
        #! Parts
        
        # S/Z row
        self.SZ = SVG.g(id="SZ")
        for item in self.draw_SZ():
            self.SZ.appendChild(item)
        self.drawing.appendChild(self.SZ)
        # Cards
        self.cards = SVG.g(id="Cards", style=grid_style)
        for item in self.draw_cards():
            self.cards.appendChild(item)
        self.drawing.appendChild(self.cards)
        # action buttons

    def get_cell_size(self):
        return [self.cell_width, self.cell_height]

    def build_grid(self):
        """
        Paths for vertical BG and cell lines.
        """
        xcount, ycount = self.size
        paths = []
        # Vert guides
        for x in range(1, xcount):
            ydist = self.dimensions[1]# + max(self.label_font_size, self.cell_width/3) if x%4 == 0 else self.dimensions[1]
            d = f"M {self.start[0]+self.cell_width*x},{self.start[1]} v {ydist}"
            paths.append(SVG.path(d=d))
        # bottom ticks (4's)
        for x in range(4, xcount+1, 4):
            if self.loom_prefs["hnumbering"] == "L2R":
                offset = self.cell_width * x
            else:
                offset = self.cell_width * (xcount-x+1)
            ydist = max(self.label_font_size, self.cell_width/3)
            d = f"M {self.start[0]+offset},{self.start[1]+self.dimensions[1]} v {ydist}"
            paths.append(SVG.path(d=d, style=red_tick_style))
        # LHS H-ticks
        for y in range(0, ycount+1):
            d = f"M {self.start[0]},{self.start[1]+self.cell_height*y} h {-self.cell_width/3}"
            paths.append(SVG.path(d=d, style=red_tick_style))
        # Angles 1 - angled lines that hit the bottom
        startx = self.start[0]+self.dimensions[0]
        starty = self.start[1]+self.dimensions[1]
        clipx = 0
        for x in range(0, xcount+1):
            xdist = x * self.cell_width
            ydist = xdist * 1/g_diamond_ratio
            #print(x, self.dimensions[1] - ydist)
            # is line being drawn too high
            if self.dimensions[1] - ydist < -0.1:
                if clipx == 0:
                    clipx = x
                ydist = self.dimensions[1] # clip Y at this point
                xdist -= (x-clipx+1) * self.cell_width  # and so adj X
            # d1 draws from bottom line up to the right
            d1 = f"M {startx-self.cell_width*x},{starty} l {xdist},{-ydist}"
            paths.append(SVG.path(d=d1))
            # d2 mirrors d1 - (draws from bottom to upper left)
            d2 = f"M {self.start[0] +self.cell_width*x},{starty} l {-xdist},{-ydist}"
            paths.append(SVG.path(d=d2))
        # Angles 2 - lines that hit the left border
        clipy = 0
        for y in range(0, self.size[1]):
            ydist = y * self.cell_height
            xdist = ydist * g_diamond_ratio
            ydist *= -1
            #print(xdist,ydist, self.dimensions[0] - xdist)
            if self.dimensions[0] - xdist < -0.1:
                if clipy == 0:
                    clipy = x
                xdist = self.dimensions[0]
                ydist += (y-clipy) * self.cell_height  # and so adj X
            # d3 draws from left border up to right border
            d3 = f"M {self.start[0]},{self.start[1]+y*self.cell_height} l {xdist},{ydist}"
            paths.append(SVG.path(d=d3))
            # d4 mirrors d3 - (draws from right side up to left border)
            d4 = f"M {startx},{self.start[1]+y*self.cell_height} l {-xdist},{ydist}"
            paths.append(SVG.path(d=d4))
        return paths

    def build_markers(self):
        xcount, ycount = self.size
        items = []
        # column lables on 4s
        for x in range(4, xcount+1, 4):
            if self.loom_prefs["hnumbering"] == "L2R":
                offset = self.cell_width * x
            else:  # R2L
                offset = self.cell_width * (xcount-x+1)
            items.append(SVG.text(f"{x}", style={"font-family":"Pathway Gothic One", "font-size":f"{self.label_font_size}"},
                                  x=self.start[0]+offset-self.label_font_width*len(str(x)),
                                  y=self.start[1]+self.dimensions[1]+self.label_font_size*1.1))
        # LHS side labels
        for y in  range(1, ycount+1):
            if self.loom_prefs["vnumbering"] == "B2T":
                offset = y * self.cell_height
            else:  # T2B
                offset = (self.size[1] - y +1) * self.cell_height
            items.append(SVG.text(f"{y}", style={"font-family":"Pathway Gothic One", "font-size":f"{self.label_font_size}"},
                                  x=self.start[0]-self.label_font_width*(len(str(y))+1),
                                  y=self.start[1]+self.dimensions[1] - offset + (self.cell_height + self.label_font_size)/2))
        return items
        
    def draw_grid(self):
        """
        Draw bg grid, row text labels, boundary rect, side buttons
        """
        # Everything is grey except where overridden
        grid_grp = SVG.g(id="BG_grid", style=grid_style)
        # This baserect used to position handle correctly after a move.
        # Must be first
        baserect = SVG.rect(x=self.start[0], y=self.start[1],
                            width=self.dimensions[0], height=self.dimensions[1],
                            style=border_style)
        grid_grp.appendChild(baserect)
        # diagonal and vert lines
        for p in self.build_grid():
            grid_grp.appendChild(p)
        # Labels
        labels_grp = SVG.g(id="grid_labels", style=label_style)
        for text in self.build_markers():
            labels_grp.appendChild(text)
        # side buttons
        buttons_grp = SVG.g(id="side_buttons", style=button_style)
        height = self.cell_height
        startx = self.start[0]+g_brdr2
        buttons = [SVG.rect(x=startx+self.size[0]*self.cell_width, y=self.start[1]+i*height,
                            rx=height/6, ry=height/6,
                            width=self.cell_width*1.3/2, height=height,
                            style=button_style) for i in range(self.size[1])]
        for b in buttons:
            buttons_grp.appendChild(b)
        return [grid_grp, labels_grp, buttons_grp]

    def draw_SZ(self):
        """
        Boxes for the S/Z row:
        - Need outline box and vertlines
        - S will be drawn on pattern layer.
        - detection is box on ui_layer
        """
        boxcount = self.size[0]
        width = self.cell_width
        height = width * 1.3
        startx = self.start[0]
        starty = self.start[1] + self.cell_height*self.size[1] + self.parts_gap + height + self.sz_gap
        rect = [SVG.rect(x=startx, y=starty, width=width*boxcount, height=height,
                          style=sz_style, id="SZbox")]
        lines = [SVG.line(x1=startx+width*i, x2=startx+width*i,
                          y1=starty, y2=starty+height,
                          style=grid_style) for i in range(1,boxcount)]
        # side button
        lines.append(SVG.rect(x=startx+g_brdr2+width*boxcount, y=starty, rx=height/6, ry=height/6,
                              width=height/2, height=height,
                              style=button_style))
        rect.extend(lines)
        return rect

    def draw_cards(self):
        """
        The card boxes with circle markers:
        - Need outline box and gridlines
        - blobs will be drawn on pattern layer.
        - detection is box on ui_layer
        """
        warpcount = self.size[0]  # number of warp threads
        holecount = self.holecount
        width = self.cell_width
        height = width * 1.3
        startx = self.start[0]
        starty = self.start[1] + self.cell_height*self.size[1] + self.parts_gap + height*2 + self.sz_gap + self.cards_gap
        items = [SVG.rect(x=startx, y=starty, width=width*warpcount, height=height*self.holecount,
                          style=sz_style, id="cardbox")]
        vlines = [SVG.line(x1=startx+width*i, x2=startx+width*i,
                          y1=starty, y2=starty+height*self.holecount)
                          for i in range(1, warpcount)]
        items.extend(vlines)
        hlines = [SVG.line(x1=startx, y1=starty+i*height,
                          x2=startx+width*warpcount, y2=starty+i*height)
                          for i in range(1, self.holecount)]
        items.extend(hlines)
        for j in range(self.holecount):
            circles = [SVG.rect(x=startx+width*i, y=starty+j*height, rx=width/2, ry = height/2,
                              width=width, height=height,
                              id=f"SZ_{i}") for i in range(warpcount)]
            items.extend(circles)
        # LHS side labels
        labels = []
        for y in range(self.holecount):
            label = self.loom_prefs["card_labels"][y]
            if self.loom_prefs["card_vert_order"] == "T2B":
                offset = height*(y+1)
            else:  # B2T
                offset = (self.holecount - y) * height
            labels.append(SVG.text(f"{label}",
                                  style={"font-family":"Pathway Gothic One", "font-size":f"{self.label_font_size}",
                                         "fill":"#000", "stroke":"none", "stroke-width": "none", "class":"unselectable"},
                                  x=startx-self.label_font_width-4,
                                  y=starty + offset - self.label_font_size/2))
        items.extend(labels)
        # col buttons
        y = starty + g_brdr2 + holecount*height
        areas = [SVG.rect(x=startx+width*i, y=y, rx=height/6, ry=height/6,
                              width=width, height=height/2,
                              style=button_style #,id=f"cardbut_{i}", #colbutrect
                              ) for i in range(warpcount)]
        items.extend(areas)
        # row buttons
        areas = [SVG.rect(x=startx+g_brdr2+width*warpcount, y=starty+i*height, rx=height/6, ry=height/6,
                              width=height/2, height=height,
                              style=button_style) for i in range(holecount)]
        items.extend(areas)
        return items


class Draft_UI_layer(object):
    """
    Holds:
     - box detecting motion over the draft,
     - mouseover diamond,
     - resizing handle
     - SZ button and region
     - Cards region
     - Parts region and control
    """
    def __init__(self, draft_bg, full_size, curr_shape_width=40):
        self.parent = draft_bg
        self.curr_shape_size = [curr_shape_width ,1/g_diamond_ratio*curr_shape_width]
        self.drawing = SVG.svg(width=full_size[0], height=full_size[1],
                         preserveAspectRatio="xMidYMid meet",
                         tabindex="-1",
                         viewBox=f"0 0 {full_size[0]} {full_size[1]}")
        #
        self.handle = SVG.g(id="size_handle")
        self.handle_min_w = 28  #! don't let handle box get smaller
        for part in self.build_size_handle():
            self.handle.appendChild(part)
        self.drawing.appendChild(self.handle)
        #
        baserect = SVG.rect(x=self.parent.start[0], y=self.parent.start[1],
                            width=self.parent.dimensions[0], height=self.parent.dimensions[1],
                            style=unseen_style, id="baserect")
        self.base = SVG.g(id="base")
        self.base.appendChild(baserect)
        self.drawing.appendChild(self.base)
        # control position of diamonds with transform
        self.diamond_grp = SVG.g(id="diamonds", transform='translate(100 100)', style=highlight_style)
        self.drawing.appendChild(self.diamond_grp)
        self.d_ids = []  # used to remove when replacing on resize
        diamonds = self.build_diamonds()  # current cell size
        for d in diamonds:
            self.diamond_grp.appendChild(d)
            self.d_ids.append(f"#{d.attributes['id']}")
        # active shapes resources
        w,h = self.curr_shape_size
        self.curr_shapes = SVG.svg(width=w, height=h,
                    preserveAspectRatio="xMidYMid meet",
                    tabindex="-1",
                    viewBox=f"-{w-3} -{h*2} {w+2} {h*2}")
        self.shapes_grp = SVG.g(id="shapes", style=diamond_style)
        self.curr_shapes.appendChild(self.shapes_grp)
        diamonds = self.build_diamonds(False, "sh_", self.curr_shape_size)
        for d in diamonds:
            self.shapes_grp.appendChild(d)
        # highlight
        self.highlight_grp = SVG.g(id="highlight", transform='translate(100 100)', style=highlight_style)
        self.drawing.appendChild(self.highlight_grp)
        width = self.parent.cell_width
        height = width * 1.3
        rects = [SVG.rect(x=0, y=0, width=width, height=height, id="highrect"),
                 SVG.rect(x=0, y=0, width=height/2, height=height, rx=height/6, ry=height/6, id="highlozV"),
                 SVG.rect(x=0, y=0, width=width, height=height/2, rx=height/6, ry=height/6, id="highlozH"),
                 SVG.rect(x=0, y=0, width=height/2, height=self.parent.cell_height, rx=height/6, ry=height/6, id="highlozC")]
        for r in rects:
            self.highlight_grp.appendChild(r)
        # SZ
        self.sz_grp = SVG.g(id="slant")
        boxcount = self.parent.size[0]
        startx = self.parent.start[0]
        starty = self.get_sz_starty()
        rect = SVG.rect(x=startx, y=starty, width=width*boxcount, height=height,
                          style=unseen_style, id=f"szrect")
        self.sz_grp.appendChild(rect)
        self.drawing.appendChild(self.sz_grp)
        # Parts - #partsrect
        self.card_grp = SVG.g(id="cards")
        holecount = self.parent.holecount
        starty = self.get_card_starty()
        rect = SVG.rect(x=startx, y=starty, width=width*boxcount, height=height*holecount,
                          style=unseen_style, id=f"cardrect")
        self.card_grp.appendChild(rect)
        self.drawing.appendChild(self.card_grp)
        # Selection/targets
        self.sel_positions = []
        self.sel_grp = SVG.g(id="sel", style=highlight_style)
        self.drawing.appendChild(self.sel_grp)
        # this is for targets of selections
        self.sel_targets_grp = SVG.g(id="sel_targets", style=target_style)
        self.drawing.appendChild(self.sel_targets_grp)
        # this is for mouseover targets
        self.target_grp = SVG.g(id="targets", style=target_style)
        self.drawing.appendChild(self.target_grp)
        # Action buttons
        self.btn_grp = SVG.g(id="btns", style=button_style)
        self.drawing.appendChild(self.btn_grp)
        y = self.get_card_endy()+g_brdr2
        card_butbelow = SVG.rect(x=startx+g_brdr2, y=y,
                              width=width*boxcount, height=height/2,
                              style=unseen_style, id="card_butbelow_rect")
        self.btn_grp.appendChild(card_butbelow)
        card_butside = SVG.rect(x=startx+g_brdr2+width*boxcount, y=starty,
                              width=height/2, height=height*holecount,
                              style=unseen_style, id="card_butside_rect")
        self.btn_grp.appendChild(card_butside)
        starty = self.get_sz_starty()
        sz_sidebutton = SVG.rect(x=startx+g_brdr2*2+width*boxcount, y=starty,
                              width=height/2, height=height,
                              style=unseen_style, id="sz_butside_rect")
        self.btn_grp.appendChild(sz_sidebutton)
        cells_sidebutton = SVG.rect(x=self.parent.start[0]+self.parent.dimensions[0],
                              y=self.parent.start[1],
                              width=height/2, height=self.parent.dimensions[1],
                              style=unseen_style, id="cells_butside_rect")
        self.btn_grp.appendChild(cells_sidebutton)
                            
        # work out how to do DnD of a column
        # - work out how to follow a split vert column

        

        
    # detection boxes
    def get_cells_endy(self):
        return self.parent.start[1] + self.parent.cell_height*self.parent.size[1]
        
    def get_sz_starty(self):
        height = self.parent.cell_width * 1.3
        start = self.parent.start[1] + self.parent.cell_height*self.parent.size[1]
        start += self.parent.parts_gap + height + self.parent.sz_gap
        return start

    def get_card_starty(self):
        height = self.parent.cell_width * 1.3
        start = self.get_sz_starty()
        start += height + self.parent.cards_gap
        return start

    def get_card_endy(self):
        return self.get_card_starty() + self.parent.holecount * self.parent.cell_width * 1.3

    def update_detection_boxes(self):
        """
        Respecify pos,size of sz,card,buttons detection boxes
        - used by finalise_draft_move()
        """
        result = []
        startx = self.parent.start[0]# + g_brdr2
        cell_width = self.parent.cell_width
        # SZ
        boxcount = self.parent.size[0]
        width = cell_width * boxcount
        height = cell_width * 1.3
        starty = self.get_sz_starty()
        rect_values = [["#szrect",'x',startx],["#szrect",'y',starty],
                       ["#szrect",'width',width],["#szrect",'height',height]]
        result.extend(rect_values)
        # sz button
        rect_values = [["#sz_butside_rect",'x',startx+g_brdr2+width],["#sz_butside_rect",'y',starty+g_brdr1],
                       ["#sz_butside_rect",'width',height/2],["#sz_butside_rect",'height',height]]
        result.extend(rect_values)
        # Cards
        holecount = self.parent.holecount
        starty = self.get_card_starty()
        rect_values = [["#cardrect",'x',startx],["#cardrect",'y',starty],
                       ["#cardrect",'width',width],["#cardrect",'height',height*holecount]]
        result.extend(rect_values)
        # rowbuttons
        rect_values = [["#card_butside_rect",'x',startx+g_brdr2*2+width],["#card_butside_rect",'y',starty+g_brdr1],
                       ["#card_butside_rect",'width',height/2],["#card_butside_rect",'height',height*holecount]]
        result.extend(rect_values)
        # colbuttons
        starty = self.get_card_endy() + g_brdr2
        rect_values = [["#card_butbelow_rect",'x',startx+g_brdr1],["#card_butbelow_rect",'y',starty+g_brdr1],
                       ["#card_butbelow_rect",'width',width],["#card_butbelow_rect",'height',height/2]]
        result.extend(rect_values)
        # Cell buttons "cells_butside_rect"
        starty = self.parent.start[1] + g_brdr2
        rect_values = [["#cells_butside_rect",'x',startx+g_brdr2*2+width],["#cells_butside_rect",'y',starty],
                       ["#cells_butside_rect",'width',cell_width*1.3/2],["#cells_butside_rect",'height',self.get_cells_endy()]]
        result.extend(rect_values)
        return result
        
    # Handle
    def calc_handle_position(self):
        """
        Where will the handle initially appear.
        - used by get_handle_size()
        """
        return [self.parent.start[0]+self.parent.dimensions[0] + self.parent.cell_height/2 + g_brdr2*2,
                self.parent.start[1]+self.parent.get_cell_size()[1] * (self.parent.size[1] - 2)]

    def get_handle_size(self):
        """
        get position size of handle box
        - used in update_handle(), build_size_handle()
        """
        x,y = self.calc_handle_position()
        cell_size = self.parent.get_cell_size() # max(self.handle_min_w, 
        #box_width = max(self.handle_min_w, cell_size[0] * 1.5)
        box_width = cell_size[0] * 1.5
        box_height = box_width #cell_size[1]
        return [x,y, box_width, box_height]

    def update_handle(self, newpos=[]):
        """
        update the handle svg
        return list of [id,slot,value]
        if newpos then updating during a scale drag
         - so ignore rect adjustments
         - used in resize_draft(), finalise_draft_move()
        """
        result = []
        if newpos:
            startx,starty,w,h = newpos
        else:
            startx,starty,w,h = self.get_handle_size()
        offset = w/6
        arrow_len = offset*0.8
        if not newpos:
            rect_values = [["#handle",'x',startx],["#handle",'y',starty],
                           ["#handle",'width',w],["#handle",'height',h]]
            result.extend(rect_values)
        line_values = [["#hnd_L1", 'x1', startx+offset],["#hnd_L1",'y1', starty+offset],
                       ["#hnd_L1", 'x2', startx+w-offset],["#hnd_L1",'y2', starty+h-offset],
                       ["#hnd_L2", 'x1', startx+offset],["#hnd_L2",'y1', starty+h-offset],
                       ["#hnd_L2", 'x2', startx+w-offset],["#hnd_L2",'y2', starty+offset],
                       ["#hnd_H1", 'x1', startx+w-offset-arrow_len],["#hnd_H1", 'y1', starty+h-offset],
                       ["#hnd_H1", 'x2',startx+w-offset],["#hnd_H1", 'y2',starty+h-offset],
                       ["#hnd_H2", 'x1', startx+w-offset-arrow_len],["#hnd_H2", 'y1', starty+offset],
                       ["#hnd_H2", 'x2',startx+w-offset],["#hnd_H2", 'y2',starty+offset],
                       ["#hnd_V1", 'x1', startx+w-offset],["#hnd_V1", 'y1', starty+h-offset],
                       ["#hnd_V1", 'x2',startx+w-offset],["#hnd_V1", 'y2',starty+h-offset-arrow_len],
                       ["#hnd_V2", 'x1', startx+w-offset],["#hnd_V2", 'y1', starty+offset],
                       ["#hnd_V2", 'x2',startx+w-offset],["#hnd_V2", 'y2',starty+offset+arrow_len]
                       ]
        result.extend(line_values)
        return result

    def build_size_handle(self):
        """
        Handle that allows user to rescale Draft
         - too much detail but maybe just enough
         - used by init
        """
        startx, starty, w, h = self.get_handle_size()
        offset = w/6
        arrow_len = offset*0.8
        # components
        r = SVG.rect(x=startx, y=starty, rx=4,ry=4, width=w, height=h,
                     style=handle_box_style, id="handle")
        # need own group so can be pointer ignored in css
        self.hdl_grp = SVG.g(id="int_lines")
        #self.handle.appendChild(self.hdl_grp)
        line1 = SVG.line(x1=startx+offset, y1=starty+offset,
                         x2=startx+w-offset, y2=starty+h-offset,
                         style=handle_line_style, id="hnd_L1")
        line2 = SVG.line(x1=startx+offset, y1=starty+h-offset,
                         x2=startx+w-offset, y2=starty+offset,
                         style=handle_line_style, id="hnd_L2")
        arrowH1 = SVG.line(x1=startx+w-offset-arrow_len, y1=starty+h-offset,
                           x2=startx+w-offset, y2=starty+h-offset,
                           style=handle_line_style, id="hnd_H1")
        arrowH2 = SVG.line(x1=startx+w-offset-arrow_len, y1=starty+offset,
                           x2=startx+w-offset, y2=starty+offset,
                           style=handle_line_style, id="hnd_H2")
        arrowV1 = SVG.line(x1=startx+w-offset, y1=starty+h-offset,
                           x2=startx+w-offset, y2=starty+h-offset-arrow_len,
                           style=handle_line_style, id="hnd_V1")
        arrowV2 = SVG.line(x1=startx+w-offset, y1=starty+offset,
                           x2=startx+w-offset, y2=starty+offset+arrow_len,
                           style=handle_line_style, id="hnd_V2")
        self.hdl_grp.appendChild(line1)
        self.hdl_grp.appendChild(line2)
        self.hdl_grp.appendChild(arrowH1)
        self.hdl_grp.appendChild(arrowH2)
        self.hdl_grp.appendChild(arrowV1)
        self.hdl_grp.appendChild(arrowV2)
        return [r, self.hdl_grp]
    
    # Diamonds
    def replace_diamonds(self):
        """
        Remake the diamonds after rescale to fit
        - used by finalise_draft_move()
        """
        diamonds = self.build_diamonds(True)  # build in the dom
        for i,d in enumerate(self.d_ids):
            ltk.find(d).remove()  # remove the existing ones
            dia = diamonds[i]
            ltk.window.document.querySelector("#diamonds").appendChild(dia)

    def build_diamonds(self, indom=False, prefix="", size=[]):
        """
        Build the [L,R,H,Q,zero] diamond paths
        - and the 2,3,4 column shift diamonds
        - indom flag builds for replacing live in dom (on resize)
        If prefix and size then used by active widget
        - used by init(x2) and replace_diamonds()
        """
        if size:
            width = size[0]
            height = size[1]
        else:
            width, height = self.parent.get_cell_size()
        #
        dL = f"M 0,0 v {-height} l {-width},{-height} v {height} z"
        dR = f"M {-width},0 v {-height} l {width},{-height} v {height} z"
        pathL = SVG.path(d=dL, id=f"{prefix}diamond_L")
        pathR = SVG.path(d=dR, id=f"{prefix}diamond_R")
        # add in the L,R,skip,H,Q variants and control with opacity
        if indom:
            pathL = SVG.todom(pathL)
            pathR = SVG.todom(pathR)
        return [pathL, pathR]

    def set_diamond_style(self, style):
        " change color with style "
        self.diamond_grp.style = style  #! but jquery or document

    def set_diamond(self, where="mouse", mode="L"):
        """
        Set only one diamond visible in:
        - the Active shape area, or
        - 'under the mouse' in cells region
        - ued by enter_cell(), leave_cell(), draft_keydown(), cycle_active_shape()
        """
        name = f"#diamond_{mode}"
        if not mode:  # make under mouse invisible
            ltk.window.document.querySelector("#diamonds").setAttribute("opacity",0)
        else:
            if where == "mouse":
                ltk.window.document.querySelector("#diamonds").setAttribute("opacity",1)
            #
            for id in self.d_ids:
                # which ids are we modifying ("mouse" or "active")
                shape_id = id if where == "mouse" else "#sh_"+id[1:]
                if id == name:
                    ltk.window.document.querySelector(shape_id).setAttribute('opacity', 1)
                else:
                    ltk.window.document.querySelector(shape_id).setAttribute('opacity', 0)

    def create_box(self, region, coord):
        """
        Given a region and a coord:
        - return an in-dom rect for drawing
        Used when adding to selections
        """
        xstart = g_brdr2+self.parent.start[0]
        ystart = g_brdr2
        width = self.parent.cell_width
        height = 1.3 * width
        id = f"H_{region}_{coord[0]}_{coord[1] if len(coord)>1 else 0}"
        if "sz" == region:
            bbox = ltk.find("#slant").children()[0].getBBox()
            ystart += bbox.height + bbox.y
            x = xstart + (coord[0]) * width
            y = ystart - (coord[1]+1) * height
            rect = SVG.todom(SVG.rect(x=x, y=y, width=width, height=height, id=id))
        elif "cards" == region:
            bbox = ltk.find("#cards").children()[0].getBBox()
            ystart += bbox.height + bbox.y
            x = xstart + (coord[0]) * width
            y = ystart - (coord[1]+1) * height
            rect = SVG.todom(SVG.rect(x=x, y=y, width=width, height=height, id=id))
        else:  # cells
            bbox = ltk.find("#base").children()[0].getBBox()
            ystart += bbox.height + bbox.y
            x = xstart + (coord[0]) * width
            if len(coord)==1:  # column
                height = self.parent.size[1]*self.parent.cell_height
                rect = SVG.todom(SVG.rect(x=x, y= bbox.y, width=width, height=height, id=id))
            else:  # one cell
                height = self.parent.cell_height
                y = ystart - (coord[1]+1) * height
                rect = SVG.todom(SVG.rect(x=x, y=y, width=width, height=height, id=id))
        return rect


#! need class to control draft in another file.

class Pattern(object):
    """
    Pattern stores the visual drawn pattern
    - organised as a dict of columns
    - actually turn designations like F,B,..
    Also:
    - SZ per ccolumn values
    - card colors
    """
    def __init__(self, draft_bg, full_size):
        self.parent = draft_bg  # a Draft_bg for sizing
        self.drawing = SVG.svg(width=full_size[0], height=full_size[1],
                         preserveAspectRatio="xMidYMid meet",
                         viewBox=f"0 0 {full_size[0]} {full_size[1]}")
        #
        self.pattern = {}  # columns
        self.pieces = SVG.g(id="cells")
        self.drawing.appendChild(self.pieces)

    # probably want a special overlay piece we can keep redrawing and seting opacity of to hide.
    # Could draw active cell in UI layer ?
    # this is sep from drawing diamonds into the system (with ids based on cells so we can delete, move enmasse)
    def draw_diamond(self, pos, style=style):
        width,height = self.parent.get_cell_size()
        d = f"M {self.parent.start[0]+pos[0]*width},{self.parent.start[0]+pos[1]*width} v -{height} l -{width},-{height} v {height} z"
        path = SVG.path(d=d, style=style, id="active_cell")
        return path

# https://stackoverflow.com/questions/3492322/javascript-createelementns-and-svg

# moves (stored in pattern, visualised in diamonds)
# - S means skip (or zero).
# Picks are a separate pass and can happen before/after a move
# Cards - can turn 1/8th (point up). Spreads into an upper shed and lower shed
# Weft section:
#  - Normal - like Inkle, 
#  - Start in from edge - like Tubular selvedge,
#  - Multishuttle - like Embroidery.
# Rendering:
#  - enable folded under - like tubular,
#  - enable round - like Rope style - weft always in one direction. (1/8 turn)
# Draw central vertical line in BG