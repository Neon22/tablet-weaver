import ltk
from tablet_widget import *
from tablet_weaver import *
from pyscript import PyWorker


#Todo
# - diamond offsets x2,3,4 - not in loop control (will be DnD)
# - clip sel when resizing draft rebuild_selection()
# - space to clear selection (a single input focussed)
# - "dblclick" clears cell or card (no effect in sz)
# - targets working and Tablet-weaver integrated

# - autoname based on params if no name entered
# - r-click ("contextmenu") are we doing a menu?
# feedback area:
#   - E.g. all S - will have coiling/spiralling of relaxed band.
# stats area:
#   - warps not all same twist so some ends undermore tension nand longer warp.
#   - length of colors used - assoc with a selection. e.g. variant, render rpt seq
#     When showing a pattern variant - show length of cord for that color
#   - show groups of cards that can be speedwarped
# Card Threading viewer:
#  - one line which expands vertically to show cards.
#  - focus(scaleup) as mouse rolls over cards
#  - Do we want separate one for action of threading cards
#    - with arrow keys to move

# Tutorial - workflows.
#  - 1. Intro:
#     - set width. Populate colors.
#     - Choose from layout (SZ, borders) (adjust layout to suit)
#       - layout should also include balance SZ about center
#     - set repeats in band visualizer
#     - adjust colors for interest features
#     - adjust directions for interest
# Missing hole variants done by removing a color (dblclick)
#  - bit like a pick - weft shows (texture)
# Want an easy way to turn all cards (button on LHS of each row?)
#  - also have to make space for weft button on each row (RHS)
# Pattern view/Turning diagram:
#  - show graphical version. text version option
#  - show F,B in each row with shaded BG and turning points line
#   - options to not show a turning point line
# Weaving Viewer:
#  - separate pane with space bar to step forward
# Repeats:
#  - auto detect repeats
#  - allow user to manually adjust (also show where we think it is)
#  - show markers on LHS ,grey out over cells above repeat line
#  - update visualizers: repeats,floats,pattern,variants
# Warp calc:
#  - desired length * 1.2 (interlacing adj) + 0.3m waste = warp length
# Double weave:
#  - can double height of cell and remove even numbers. (will preserve aspect ratio)
# Inverting copy:
#  - Useful to take a repeat, copy it above but reverse F/B (will be mirrored)
#  - resulting band will be straighter and not coil as much??
# hex cards:
#  - two ways to align:
#    - point up - central shed(2 small sheds)
#      - squished (more compressed) pattern, band wider but thinner
#    - flat on top - upper and lower shed. Through one and back the other
#      - wide pattern, narrower band but thicker
# Speedwarping:
#  - possible if all cards can be rotated into identical layouts.
#  - not possible if they can't.
#  - can indicate which(+ counts) cards can be speedwarped


# For debugging purposes
ltk.window.document.currentScript.terminal.resize(60, 10)
#def print(*args):
#    ltk.find("body").append(" ".join(str(a) for a in args), "<br>")
print("Hello, World!")


loom = None  # global object for active Loom_widget object
# These 3 track resize handle.
g_h_selected = None
g_h_selected_offset = None
g_h_offset = None
# These track current mouseover cell
g_cell_over = None
g_cell_prev = [-1,-1]  # holds prev value to avoid unneccessary redraws
# for cycling through the chosen subset of directions
g_cell_angles = ["L","R","L"] #["L","R","H","Q","zero","L"]
g_cell_angle = "L"
# regions
g_active_region = None


# Card Labels  (prefs)
card_label_sets = [["A","B","C","D","E","F"],["1","2","3","4","5","6"],
                      ["Vu","Vo","Hu","Ho","E","F"]]
# initial palette
g_palette = {"starter": ["a default palette", "ffbe6f","cdab8f","f4cff4f","bccee4",
                       "6fa7ec","2f42e1"]}

# Patch ltk.SplitPane
class MySplitpane(ltk.HorizontalSplitPane):
    """
    Add a px offset to calc position
    - get_position(), set_position()
    - get_size(),  set_size()
    """
    def __init__(self, first, last, key, offset_fcn=None):
        self.offset_fcn = offset_fcn
        super().__init__(first, last, key)

    def resize(self):
        size = self.get_size(self)
        if self.offset_fcn:
            position = self.offset_fcn()
        else:
            position = self.get_position(self.middle) - self.get_position(self)
        if size:
            percentage = round(100 * position / size)
            self.layout(percentage)

def get_split_position(el_id="split_1"):
    """
    Find the width of the VBox on LHS of the Splitplane
    """
    el = ltk.find(f"#{el_id}")
    # left is harder to determine than width
    bounds = ltk.window.document.getElementById(el_id).getBoundingClientRect()
    width = el.width()# - bounds.left
    print(el_id, el.width(),bounds.left)
    return width

def start_splitmove(event):
    """
    setup to shadow drag
    """
    global g_h_selected, g_h_selected_offset
    g_h_selected = event.target
    g_h_selected_offset = get_split_position("split_1")
    print("Start", g_h_selected_offset)
    if loom.current_selection:
        loom.clear_selection()
    # ignore the cell row detection box (we collide)
    ltk.find("#cells_butside_rect").addClass("ignored")
    #! empty the pattern

def shadow_splitmove(event,ui):
    """
    Shadow mouse drag of splitter handle
    """
    global g_h_selected_offset
    if g_h_selected:
        left = ltk.find(event.target).css("left")
        print(left,left.split("p"))
        offset = int(left.split("p")[0])
        width = g_h_selected_offset + offset
        #
        svg = loom.create_draft_bg(offset)# - loom.startpos[0])#x-g_h_offset[0])
        ltk.find("#draft_bg").html(svg) 
        # resize the baserect box
        grid_bbox = ltk.find("#BG_grid").children()[0].getBBox()
        loom.resize_draftUI_box(grid_bbox)

        
def end_splitmove(event):
    global g_h_selected
    if g_h_selected:
        bbox = ltk.find("#BG_grid").children()[0].getBBox()
        # reset self.draft_width variable etc
        loom.draft_width = bbox.width
        loom.finalise_draft_move()
        g_h_selected = None
        #! redraw the drawn selection,highlights
        if loom.current_selection:
            loom.rebuild_selection()
        # reenable cell collision box
        ltk.find("#cells_butside_rect").removeClass("ignored")
        #! redraw the pattern

def get_mouse_position(event, el):
    """
    Get the screen coords of the mouse
    - for dragging events
    """
    CTM = el.getScreenCTM()
    x = (event.clientX - CTM.e) / CTM.a
    y = (event.clientY - CTM.f) / CTM.d
    return [x,y]

def start_drag(event):
    """
    Used when we want to Drag:
    - calc offsets for simple math adj of moving element
    """
    global g_h_selected, g_h_selected_offset, g_h_offset
    g_h_selected = event.target
    print(event.target)
    g_h_offset = get_mouse_position(event, g_h_selected)
    g_h_selected_offset = get_mouse_position(event, g_h_selected)
    #print("start resize", g_h_offset)
    g_h_selected_offset[0] -= float(g_h_selected.getAttributeNS(None,"x"))
    g_h_selected_offset[1] -= float(g_h_selected.getAttributeNS(None,"y"))

def resize_draft_start(event):
    """
    Setup to start dragging the handle.
    - hide pattern maybe ? #!
    """
    #event.preventDefault()
    start_drag(event)
    #! empty the drawn selection,targets
    if loom.current_selection:
        loom.clear_selection()
    # ignore the cell row detection box (we collide)
    ltk.find("#cells_butside_rect").addClass("ignored")
    #! empty the pattern

def resize_draft(event):
    """
    Active mouse motion while dragging
    - resize the draft_bg etc
    - g_h_selected will be "#handle"
    """
    #event.preventDefault()
    if g_h_selected:
        x,y = get_mouse_position(event, g_h_selected)
        #! check and clamp to max,min size
        #print("resize me", x-g_h_offset[0], y-g_h_offset[1])
        offset = [x - g_h_selected_offset[0], y - g_h_selected_offset[1]]
        #! Maybe Quantize to steps > 5 (would draw less often)
        # reposition handle box
        g_h_selected.setAttributeNS(None, "x", offset[0])
        g_h_selected.setAttributeNS(None, "y", offset[1])
        #
        #if x < 250: x = 250  #! needs to be in terms of box size
        svg = loom.create_draft_bg(x-g_h_offset[0])
        ltk.find("#draft_bg").html(svg) 
        # resize the baserect box
        grid_bbox = ltk.find("#BG_grid").children()[0].getBBox()
        loom.resize_draftUI_box(grid_bbox)
        # redraw handle box and interior
        # get curr handle w,h for handle redraw
        w = float(g_h_selected.getAttribute("width"))
        h = float(g_h_selected.getAttribute("height"))
        offset.extend([w,h])
        for [id,slot,value] in loom.draft_ui_layer.update_handle(offset):
            ltk.window.document.querySelector(id).setAttribute(slot, value)

def resize_draft_end(event):
    """
    Cleanup when dropping resize handle:
    - set grid size for redraws,
    - redraw handle in correct pos
    """
    global g_h_selected
    if g_h_selected:
        #print("end resize", get_mouse_position(event, g_h_selected))
        # need to reset the handle to proper place
        bbox = ltk.find("#BG_grid").children()[0].getBBox()
        # reset self.draft_width variable etc
        loom.draft_width = bbox.width
        loom.finalise_draft_move()
        g_h_selected = None
        #! redraw the drawn selection,highlights
        if loom.current_selection:
            loom.rebuild_selection()
        # reenable cell collision box
        ltk.find("#cells_butside_rect").removeClass("ignored")
        #! redraw the pattern

### Region actions
def enter_cell(event):
    """
    Starting mouseover
    - make diamond visible (curr active shape)
    """
    global g_active_region
    #print("-Enter cell")
    g_active_region = "cells"
    loom.draft_ui_layer.set_diamond("mouse", g_cell_angle)
    
def detect_cell(event):
    """
    mouseover draft
    - detect which cell affected
    - draw overlay of current active shape
    """
    global g_cell_over, g_cell_prev
    #print("detect cell")#event.target)
    modifier = [event.shiftKey,event.ctrlKey]
    bbox = ltk.find("#base").children()[0].getBBox()
    x,y = get_mouse_position(event, event.target)
    xcell = int((x-loom.startpos[0]) / (bbox.width/loom.draft_bg.size[0]))
    ycell = int((loom.draft_ui_layer.get_cells_endy()-y - loom.draft_bg.cell_height/2) / (bbox.height/loom.draft_bg.size[1]))
    ycell = min(ycell, loom.cells[1]-1)
    if loom.loom_prefs["vnumbering"] == "T2B":
        ycell = max(ycell, 1)  # nope. more complex now sigh
    #print("cells:",xcell, ycell, loom.cells[1]-ycell-1, y)
    if xcell == g_cell_prev[0] and ycell == g_cell_prev[1]:
        pass  # avoid unneccessary redraws
    else:
        g_cell_over = [xcell, ycell]
        g_cell_prev = [xcell, ycell]
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)

def leave_cell(event):
    """
    Hide the diamond mouseover
    """
    global g_cell_over, g_cell_prev, g_active_region
    loom.draft_ui_layer.set_diamond("mouse", None)
    g_cell_over = None
    g_cell_prev = [-1,-1]
    g_active_region = None
    #print("-Left cell")

def store_diamond(event):
    if event.shiftKey:
        print("selected", g_cell_over)
        loom.add_selection(g_active_region, [g_cell_over])
    else:  # click
        print("-store cell", g_cell_over)

def draft_keydown(event):
    " change active diamond - cycle"
    global g_cell_angle
    #print(event.key)
    if event.key == 'ArrowUp':
        g_cell_angle = g_cell_angles[g_cell_angles.index(g_cell_angle)+1]
    elif event.key == 'ArrowDown':
        g_cell_angle = g_cell_angles[g_cell_angles[1:].index(g_cell_angle)+1]
    loom.draft_ui_layer.set_diamond("mouse", g_cell_angle)
    loom.draft_ui_layer.set_diamond("active", g_cell_angle)

def cycle_active_shape(event):
    " change active diamond for next use"
    global g_cell_angle
    g_cell_angle = g_cell_angles[g_cell_angles.index(g_cell_angle)+1]
    #print("active:",g_cell_angle)
    loom.draft_ui_layer.set_diamond("active", g_cell_angle)

def enter_szcell(event):
    " entered szrect. setup"
    global g_active_region
    #print("-Enter cell")
    g_active_region = "sz"

def detect_szcell(event):
    """
    mouseover sz region
    - detect which cell affected
    - draw current sz highlight
    - second click means swap
    """
    global g_cell_over, g_cell_prev
    #print("detect szcell",g_cell_over, g_cell_prev)
    modifier = [event.shiftKey,event.ctrlKey]
    x,y = get_mouse_position(event, event.target)
    szcell = [int((x-loom.startpos[0]-g_brdr2) / loom.draft_bg.cell_width),0]
    if not g_cell_over or szcell != g_cell_prev:  # avoid unneccessary redraws
        g_cell_over = szcell
        g_cell_prev = szcell
        # draw blob over the cell + targets
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)

def leave_a_cell(event):
    """ 
    Leaving one of the non diamond cells: 
    - Hide the mouseover box
    - clear the mouseover globals
    """
    global g_cell_over, g_cell_prev, g_active_region
    g_cell_over = None
    g_cell_prev = [1,-1]
    g_active_region = None
    loom.draw_highlight_over(None,None,None, True)  # clear

def store_sz(event):
    " clicked on szrect. store current sz"
    if event.shiftKey:
        print("selected", g_cell_over)
        loom.add_selection(g_active_region, [g_cell_over])
    else:  # click
        print("-store sz", g_cell_over)

#
def enter_cardcell(event):
    " entered cardrect. setup"
    global g_active_region
    #print("-Enter cell")
    g_active_region = "cards"

def detect_cardcell(event):
    """
    mouseover cards region
    - detect which cell affected
    - draw current card highlight
    - second click means swap
    """
    global g_cell_over, g_cell_prev
    #print("detect szcell",g_cell_over, g_cell_prev)
    modifier = [event.shiftKey,event.ctrlKey]
    x,y = get_mouse_position(event, event.target)
    cell_height = loom.draft_bg.cell_width * 1.3
    xcell = int((x-loom.startpos[0]-g_brdr2) / loom.draft_bg.cell_width)
    ycell = int((loom.draft_ui_layer.get_card_endy()-y-g_brdr2) / cell_height)
    # avoid unneccessary redraws
    if not g_cell_over or xcell != g_cell_prev[0] or ycell != g_cell_prev[1]:
        g_cell_over = [xcell, ycell]
        g_cell_prev = [xcell, ycell]
        # draw blob over the cell + targets
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)

def store_card(event):
    if event.shiftKey:
        print("selected", g_cell_over)
        loom.add_selection(g_active_region, [g_cell_over])
    else:  # click
        print("-store card", g_cell_over)

def enter_cardcol(event):
    global g_active_region
    g_active_region = "cardcol"

def select_cardcol(event, clicked=False):
    """
    called for mouseover, click and when dragging
    """
    global g_cell_over, g_cell_prev
    if g_h_selected:  # dragging
        x,y = get_mouse_position(event, g_h_selected)
        #! check and clamp to max,min size
        offset = [x - g_h_selected_offset[0], y - g_h_selected_offset[1]]
        #! Maybe Quantize to steps > 5 (would draw less often)
        print("-Dragging",x,y,offset)
        # reposition item (entire column)
        g_h_selected.setAttributeNS(None, "x", offset[0])
        g_h_selected.setAttributeNS(None, "y", offset[1])
        # If not in inital locn then need to swap it with R/L col
        #
    else:  # not dragging - mouseover or click
        modifier = [event.shiftKey,event.ctrlKey]
        x,y = get_mouse_position(event, event.target)
        xcell = int((x-loom.startpos[0]-g_brdr2) / loom.draft_bg.cell_width)
        # avoid unneccessary redraws / detect motion
        if not g_cell_over or xcell != g_cell_prev[0]:
            g_cell_over = [xcell, 0]
            g_cell_prev = [xcell, 0]
            loom.draw_highlight_over(g_active_region, g_cell_over, modifier)
        if clicked:
            loom.add_selection("cards", [[xcell,i] for i in range(loom.holecount)])

def start_drag_cardcol(event):
    start_drag(event)
    print("Started dragging")
def end_drag_cardcol(event):
    global g_h_selected
    if g_h_selected:
        g_h_selected = None
    print("dropped")


def enter_cardrow(event):
    global g_active_region
    g_active_region = "cardrow"

def select_cardrow(event, clicked=False):
    global g_cell_over, g_cell_prev
    modifier = [event.shiftKey,event.ctrlKey]
    x,y = get_mouse_position(event, event.target)
    cell_height = loom.draft_bg.cell_width * 1.3
    ycell = int((loom.draft_ui_layer.get_card_endy()-y) / cell_height)
    # avoid unneccessary redraws
    if not g_cell_over or ycell != g_cell_prev[1]:
        g_cell_over = [0, ycell]
        g_cell_prev = [0, ycell]
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)
    if clicked:
        loom.add_selection("cards", [[i,ycell] for i in range(loom.cells[0])])

def enter_szrow(event):
    global g_active_region
    g_active_region = "szrow"

def select_szrow(event, clicked=False):
    global g_cell_over, g_cell_prev
    modifier = [event.shiftKey,event.ctrlKey]
    #x,y = get_mouse_position(event, event.target)
    #height = loom.draft_bg.cell_width * 1.3
    ycell = 0#int((loom.draft_ui_layer.get_card_endy()-y) / (loom.draft_bg.cell_height))
    #g_cell_over = [0,ycell]
    if not g_cell_over or ycell != g_cell_prev[1]:
        g_cell_over = [0, ycell]
        g_cell_prev = [0, ycell]
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)
    if clicked:
        loom.add_selection("sz", [[i,ycell] for i in range(loom.cells[0])])
    print("sz select", g_cell_over)

def enter_cellrow(event):
    global g_active_region
    g_active_region = "cellrow"

def select_cellrow(event, clicked=False):
    global g_cell_over, g_cell_prev
    modifier = [event.shiftKey,event.ctrlKey]
    x,y = get_mouse_position(event, event.target)
    cell_height = loom.draft_bg.cell_height
    ycell = int((loom.draft_ui_layer.get_cells_endy()-y) / cell_height)
    # avoid unneccessary redraws
    if not g_cell_over or ycell != g_cell_prev[1]:
        g_cell_over = [0, ycell]
        g_cell_prev = [0, ycell]
        loom.draw_highlight_over(g_active_region, g_cell_over, modifier)
    if clicked:
        loom.add_selection("cells", [[i,ycell] for i in range(loom.cells[0])])

###
def initialise_diagram():
    """
    Draft_bg, etc created but need to be inserted first time
    - run once
    """
    ltk.find("#draft_handle").html(loom.draft_ui_layer.drawing.outerHTML)
    ltk.find("#draft_bg").html(loom.draft_bg.drawing.outerHTML)
    ltk.find("#pattern_layer").html(loom.pattern_layer.drawing.outerHTML)
    ltk.find("#svg_current").html(loom.draft_ui_layer.curr_shapes.outerHTML)
    # turn off highlight elements
    ltk.window.document.querySelector("#highrect").setAttribute("opacity",0)
    ltk.window.document.querySelector("#highlozH").setAttribute("opacity",0)
    ltk.window.document.querySelector("#highlozV").setAttribute("opacity",0)
    ltk.window.document.querySelector("#highlozC").setAttribute("opacity",0)
    ltk.window.document.querySelector("#diamonds").setAttribute("opacity",0)
    # palette
    for p in g_palette:
        ltk.find("#palette-titles .title").text(f"Palette: {p}")
        pal = g_palette[p]
        ltk.find("#palette-titles .label").text(f"({pal[0]})")
        colors_el = ltk.find("#palette-colors")
        for c in pal[1:]:
            # '<div class="color-block" style="background-color: rgb(21, 52, 125);"><div class="color-code">#15347d</div></div>'
            colors_el.append(ltk.Div(ltk.Div(c).addClass("color-code")).addClass("color-block").css("background-color",f"#{c}"))
    # Colors (initial)
    colors = ltk.find("#colors_box")
    first = list(g_palette.keys())[0]
    print(first)
    col1 = g_palette[first][1]
    print(col1)
    colors.append(ltk.HBox(
                        ltk.Text("1").addClass("title"),
                        ltk.Div(ltk.Div(col1).addClass("color-code")).addClass("color-block").css("background-color",f"#{col1}"),
                        ltk.Text("0").addClass("title")
                 ).addClass("color-row"))
    
    

def hookup_events():
    """
    Handle events for resizing
    - run once
    """
    handle = ltk.find("#handle")
    print("setting up handle")
    handle.on("mousedown", ltk.proxy(lambda event: resize_draft_start(event)))
    handle.on("mousemove", ltk.proxy(lambda event: resize_draft(event)))
    handle.on("mouseup", ltk.proxy(lambda event: resize_draft_end(event)))
    handle.on("mouseleave", ltk.proxy(lambda event: resize_draft_end(event)))
    #
    draft = ltk.find("#baserect")
    print("setting up draft cell events")
    draft.on("mouseenter", ltk.proxy(lambda event: enter_cell(event)))
    draft.on("mousemove", ltk.proxy(lambda event: detect_cell(event)))
    draft.on("mouseleave", ltk.proxy(lambda event: leave_cell(event)))
    draft.on("click", ltk.proxy(lambda event: store_diamond(event)))
    #
    base =  ltk.find("#draft_handle")
    base.on("keydown", ltk.proxy(lambda event: draft_keydown(event)))
    #
    curr = ltk.find("#svg_current")
    curr.on("click", ltk.proxy(lambda event: cycle_active_shape(event)))
    #
    sizer = ltk.find("#szrect")
    print("setting up draft sz events")
    sizer.on("mouseenter", ltk.proxy(lambda event: enter_szcell(event)))
    sizer.on("mousemove", ltk.proxy(lambda event: detect_szcell(event)))
    sizer.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    sizer.on("click", ltk.proxy(lambda event: store_sz(event)))
    # sz side button
    button = ltk.find("#sz_butside_rect")
    button.on("mouseenter", ltk.proxy(lambda event: enter_szrow(event)))
    button.on("mousemove", ltk.proxy(lambda event: select_szrow(event)))
    button.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    button.on("click", ltk.proxy(lambda event: select_szrow(event,True)))
    #
    cards = ltk.find("#cardrect")
    print("setting up draft card events")
    cards.on("mouseenter", ltk.proxy(lambda event: enter_cardcell(event)))
    cards.on("mousemove", ltk.proxy(lambda event: detect_cardcell(event)))
    cards.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    cards.on("click", ltk.proxy(lambda event: store_card(event)))
    # card below buttons
    button = ltk.find("#card_butbelow_rect")
    button.on("mouseenter", ltk.proxy(lambda event: enter_cardcol(event)))
    button.on("mousemove", ltk.proxy(lambda event: select_cardcol(event)))
    button.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    button.on("mousedown", ltk.proxy(lambda event: start_drag_cardcol(event)))
    button.on("mouseup", ltk.proxy(lambda event: end_drag_cardcol(event)))
    button.on("click", ltk.proxy(lambda event: select_cardcol(event,True)))
    # card side buttons
    button = ltk.find("#card_butside_rect")
    button.on("mouseenter", ltk.proxy(lambda event: enter_cardrow(event)))
    button.on("mousemove", ltk.proxy(lambda event: select_cardrow(event)))
    button.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    button.on("click", ltk.proxy(lambda event: select_cardrow(event,True)))
    # cell side buttons
    button = ltk.find("#cells_butside_rect")
    button.on("mouseenter", ltk.proxy(lambda event: enter_cellrow(event)))
    button.on("mousemove", ltk.proxy(lambda event: select_cellrow(event)))
    button.on("mouseleave", ltk.proxy(lambda event: leave_a_cell(event)))
    button.on("click", ltk.proxy(lambda event: select_cellrow(event,True)))
    # splitter
    loom.splitter.resize()

# Workers
def draw_floats(width,height,data):
    print("got data:",width,height,data)
    # draw it

#worker = PyWorker("./worker1.py")
#worker.sync.hello = draw_floats


#Loom preferences choices
loom_prefs = {}
# - "vnumbering": "B2T"/"T2B", "hnumbering": "L2R"/"R2L"
# - "card_vert_order": "B2T"/"T2B", "card_dir": "CW"/"CCW"
# - "card_labels": ["A","B","C","D","E","F"]/["1","2","3","4"...]/["Vo","Vu","Ho","Hu"],
# - "slant_icon": "arrow"/"letter", "slant_angle": "threading"/"card"

class Loom_widget(object):
    """
    All of the onscreen series of widgets etc
    """
    def __init__(self, svg_dimensions, weaver=None, cells=[16,8], holecount=4):
        # Full svg dimensions  
        # - all svgs placed onto this stage
        self.dimensions = svg_dimensions
        self.startpos = [60,20]
        self.draft_width = 200  # needs to be 400 to scale active cell correctly :(
        self.min_box_size = 10  # start with 10 pixel wide cells
        #
        if weaver:
            self.weaver = weaver
            self.cells = [weaver.width, weaver.height]
            self.holecount = weaver.holecount
        else:
            self.cells = cells
            self.holecount = holecount
        #
        
        self.loom_prefs = {"vnumbering": "B2T", "hnumbering": "L2R",
                          "card_labels": ["A","B","C","D","E","F"],
                          "card_dir": "CW", "card_vert_order": "B2T",
                           "slant_icon": "arrow", "slant_angle": "card"
                          }
        self.current_selection = {}  # holds type and list of sel elements
        self.current_targets = []
        #
        self.draft_bg = None
        self.draft_ui_layer = None
        self.split_1_offset = 60  # used to position primary splitter
        

    
    def calc_draft_size(self, width):
        """
        Given a desired width, the aspect ratio of the diamond grid and
        the number of cells in rows and columns:
        - calculate the svg space we need to draw the draft.
        """
        #max_size = 
        return [width, width/self.cells[0]*(1/g_diamond_ratio)*self.cells[1]]

    def create_draft_bg(self, delta=0):
        """
        The user has used the resize handle.
         - we have a new size to fit
         - make a new svg for the draft_bg and return it
        """
        size = self.calc_draft_size(self.draft_width + delta)
        self.draft_bg = Draft_BG(self.startpos, size, self.dimensions, self.cells, self.holecount, self.loom_prefs)
        return self.draft_bg.drawing.outerHTML

    def resize_draftUI_box(self, bbox):
        """
        Resize the baserect to fit the scaled size.
        """
        # determine current actual draft_width
        #x,y = bbox.x, bbox.y
        width,height = bbox.width, bbox.height
        ltk.window.document.querySelector("#baserect").setAttribute('width', width)
        ltk.window.document.querySelector("#baserect").setAttribute('height', height)

    def finalise_draft_move(self):
        """
        User finished resizing. cleanup detection boxes:
        - handle,sz,cards,
        """
        self.draft_ui_layer.parent = self.draft_bg  # point it to the newest one
        # remake the diamonds
        self.draft_ui_layer.replace_diamonds()
        # resize sz and cards detection box
        for [id,slot,value] in self.draft_ui_layer.update_detection_boxes():
            ltk.window.document.querySelector(id).setAttribute(slot, value)
        # resize the #handle
        for [id,slot,value] in self.draft_ui_layer.update_handle():
            ltk.window.document.querySelector(id).setAttribute(slot, value)
        # move the slider in case shifted
        split_pos = get_split_position()
        print("Diff:",split_pos, self.draft_width)
        # remake the highlight to be new cellsize
        width = self.draft_bg.cell_width
        height = width * 1.3
        # resize highlights
        for [id,slot,value] in [["#highrect",'width', width],["#highrect",'height', height],
                                ["#highlozV",'width', height/2],["#highlozV",'height', height],
                                ["#highlozV",'rx', height/6],["#highlozV",'ry', height/6],
                                ["#highlozH",'width', width],["#highlozH",'height', height/2],
                                ["#highlozH",'rx', height/6],["#highlozH",'ry', height/6],
                                ["#highlozC",'width', height/2],["#highlozC",'height', self.draft_bg.cell_height],
                                ["#highlozC",'rx', height/6],["#highlozC",'ry', height/6]
                               ]:
            ltk.window.document.querySelector(id).setAttribute(slot, value)
 
    def adjust_cell_counts(self, event, dir):
        """
        User is manually adjusting cols,rows of draft
        """
        print("change cells:",dir,event.target.value)
        if event.target.value and int(event.target.value) > 2:
            if dir == "w":
                self.cells[0] = int(event.target.value)
            else:  # Height
                self.cells[1] = int(event.target.value)
            #! hide selection
            if loom.current_selection:
                loom.clear_selection()
            #
            print(self.cells)
            svg = self.create_draft_bg()
            ltk.find("#draft_bg").html(svg) 
            #
            grid_bbox = ltk.find("#BG_grid").children()[0].getBBox()
            self.resize_draftUI_box(grid_bbox)
            self.finalise_draft_move()
            #! redraw selection
            if loom.current_selection:
                loom.rebuild_selection()

    def draw_highlight_over(self, stype, pos, modifier, clear=False):
        """
        Draw current cell as an overlay under mouse in box
        - used by sz and cards, cells(diamonds)
        - if clear - set opacity to 0
        - Also draw targets
        """
        print("highlight-:", stype, pos)
        if clear:
            ltk.window.document.querySelector("#highrect").setAttribute("opacity",0)
            ltk.window.document.querySelector("#highlozV").setAttribute("opacity",0)
            ltk.window.document.querySelector("#highlozC").setAttribute("opacity",0)
            ltk.window.document.querySelector("#highlozH").setAttribute("opacity",0)
            ltk.find("#targets").empty()
        else:
            width = self.draft_bg.cell_width
            height = 1.3 * width
            xstart = self.draft_bg.start[0] + g_brdr2
            ystart = g_brdr2
            #
            if stype == "sz":
                bbox = ltk.find("#slant").children()[0].getBBox()
                ystart += bbox.height + bbox.y
            elif stype == "cards":
                bbox = ltk.find("#cards").children()[0].getBBox()
                ystart += bbox.height + bbox.y
            elif stype == "cardcol":
                ystart += loom.draft_ui_layer.get_card_endy() + height + g_brdr2
            elif stype == "cardrow":
                ystart += loom.draft_ui_layer.get_card_endy()
            elif stype == "szrow":
                ystart += loom.draft_ui_layer.get_sz_starty() + height
            elif stype == "cellrow":
                ystart += loom.draft_ui_layer.get_cells_endy()
            else:  # cells
                ystart += self.draft_ui_layer.get_cells_endy()
            #
            x = xstart + (pos[0]) * width
            y = ystart - (pos[1]+1) * height
            # diamonds/boxes/lozenges
            if stype == "cells":
                # diamond shapes have diff height
                x += width
                y = ystart - (pos[1]+0) * self.draft_bg.cell_height
                ltk.window.document.querySelector("#diamonds").setAttribute("transform", f"translate({x} {y})")
            elif stype == "cardcol": # lozengeH
                ltk.window.document.querySelector("#highlight").setAttribute("transform", f"translate({x} {y})")
                ltk.window.document.querySelector("#highlozH").setAttribute("opacity",1)
            elif stype == "cardrow" or stype == "szrow":  # lozengeV
                x = xstart + (width)*self.cells[0] + g_brdr2
                ltk.window.document.querySelector("#highlight").setAttribute("transform", f"translate({x} {y})")
                ltk.window.document.querySelector("#highlozV").setAttribute("opacity",1)
            elif stype == "cellrow":  # lozengeV larger cell height
                x = xstart + (width)*self.cells[0] + g_brdr2
                y = ystart - (pos[1]+1) * self.draft_bg.cell_height
                ltk.window.document.querySelector("#highlight").setAttribute("transform", f"translate({x} {y})")
                ltk.window.document.querySelector("#highlozC").setAttribute("opacity",1)
            else:  # a box (sz,cards)
                ltk.window.document.querySelector("#highlight").setAttribute("transform", f"translate({x} {y})")
                ltk.window.document.querySelector("#highrect").setAttribute("opacity",1)
            # targets
            self.draw_targets(stype, pos, modifier)
                
                
    def add_selection(self, stype, pos_list):
        """
        Add to current selection.
        All in selection must be from same region
        """
        print(stype,pos_list)
        sel_dom = ltk.find("#sel")  # onscreen in here
        if not self.current_selection:
            # make new one
            self.current_selection = {stype:pos_list}
            for pos in pos_list:
                box = self.draft_ui_layer.create_box(stype, pos)
                sel_dom.append(box)
        else:  # we have a selection already
            # is it the same type as element
            if stype in self.current_selection:
                # same type so add to selection
                for pos in pos_list:
                    if pos not in self.current_selection[stype]:
                        self.current_selection[stype].append(pos)
                        box = self.draft_ui_layer.create_box(stype, pos)
                        sel_dom.append(box)
                    else:  # in already so remove from sel
                        id = f"#H_{stype}_{pos[0]}_{pos[1] if len(pos)>1 else 0}"
                        print("Found/remove:",id)
                        self.current_selection[stype].remove(pos)
                        ltk.find(id).remove()
            else:  # replace existing selection
                self.clear_selection()
                self.current_selection = {stype:pos_list}
                for pos in pos_list:
                    box = self.draft_ui_layer.create_box(stype, pos)
                    sel_dom.append(box)
        #! add targets
        print("Curr selection:",self.current_selection)
        #self.add_targets(stype, pos)

    def rebuild_selection(self):
        """
        After a redraw - need to rebuild onscreen selection
        and for deleting from a selection ? #!
        """
        if self.current_selection:
            sel_dom = ltk.find("#sel")  # onscreen in here
            for region in self.current_selection:
                coords = loom.current_selection[region]
                for c in coords:
                    sel_dom.append(self.draft_ui_layer.create_box(region, c))
                    #! rebuild targets too
            
    def clear_selection(self):
        """
        Clear selection and targets from dom only
        - so can resize, or create new
        """
        ltk.find("#sel").empty()
        ltk.find("#sel_targets").empty()
        ltk.find("#targets").empty()

    def draw_targets(self, region, pos, modifier):
        """
        Either a single mouseover highlight (region, cell)
        or a 'selection' in a region.
        Draw in #target
        """
        seltargets_dom = ltk.find("#sel_targets")  # onscreen in here
        target_dom = ltk.find("#targets")  # onscreen in here
        if self.current_selection:
            pass
        # add on single mouseover
        if region not in ["cardcol","cardrow","szrow"]:
            targets = self.weaver.retrieve_targets(region, [pos], modifier)
        else:  # region is a button
            if region == "cardcol":
                targets = {"cards": [[pos[0],i] for i in range(self.holecount)]}
            if region == "cardrow":
                targets = {"cards": [[i,pos[1]] for i in range(self.cells[0])]}
            if region == "szrow":
                targets = {"cards": [[i,0] for i in range(self.cells[0])]}
        # draw them
        print("targets",targets)
        if targets:
            target_dom.empty()
            for region in targets:
                coords = targets[region]
                for c in coords:
                    # whole col has only X value inlist
                    target_dom.append(self.draft_ui_layer.create_box(region, c))
    
    def calc_split_pos_1(self):
        return self.startpos[0] + self.draft_width + self.split_1_offset
    
    def create(self):
        """
        """
        #
        size = self.calc_draft_size(self.draft_width)
        # sizes calculated - make all the things.
        self.draft_bg = Draft_BG(self.startpos, size, self.dimensions, self.cells, self.holecount, self.loom_prefs)
        self.cell_size = self.draft_bg.get_cell_size()  # useful to hold onto
        self.draft_ui_layer = Draft_UI_layer(self.draft_bg, self.dimensions)
        self.pattern_layer = Pattern(self.draft_bg, self.dimensions)
        #
        ltk.schedule(initialise_diagram, "draw initial")  # fill the empty DIVs
        ltk.schedule(hookup_events, "SVG hookup_events")  # connect events
        #
        palette_box = ltk.VBox(
                        ltk.HBox(
                            ltk.Text("Initial").addClass("title"),
                            ltk.Text("Description of palette").addClass("label")
                        ).attr("id","palette-titles"),
                        ltk.HBox().attr("id","palette-colors")
                      ).attr("id","palette_box").addClass("palette-row")
        #
        colors_box = ltk.VBox(
                        ltk.Text("Colors:").addClass("title")
                     ).attr("id","colors_box")
        #
        cell_box = ltk.VBox(
                        ltk.Label("Active").addClass("label_wh"),
                        ltk.HBox(
                            ltk.Div().attr("id","svg_current"),
                            ltk.Div("S").attr("id","mode_label").addClass("label_wh")
                            )
                        ).attr("id","cell_box")
        size_box = ltk.HBox(
                        ltk.Label("W").addClass("label_wh"),
                        ltk.Input(self.cells[0]).attr("type","number").attr("id", "cells_h").attr("min", "4").on("change input", ltk.proxy(lambda event: self.adjust_cell_counts(event,"w"))),
                        ltk.Label("H").addClass("label_wh"),
                        ltk.Input(self.cells[1]).attr("type","number").attr("id", "cells_w").attr("min", "2").on("change input", ltk.proxy(lambda event: self.adjust_cell_counts(event,"h")))
                        ).attr("id","size_box")
        
        parts_box = ltk.Div().attr("id","parts_box")
        #
        svg_bg = ltk.Div().attr("id","draft_bg")
        svg_handle = ltk.Div().attr("id","draft_handle")
        svg_draft = ltk.Div().attr("id","svg_pattern")
        #
        svg_pattern_box = ltk.HorizontalSplitPane(
                                ltk.VBox(
                                    ltk.TextArea("Weird stuff").addClass("textbox")
                                ),
                                ltk.VBox(
                                    ltk.TextArea("more Weird stuff").addClass("textbox")
                                ),
                                "second_split").css("width", "100%").css("height", "100vh")
                         #).attr("id","pattern_box")
        #
        self.splitter = MySplitpane(
             ltk.VBox(
                 ltk.HBox(  # Editor
                     svg_bg, svg_draft, svg_handle
                 ).attr("id","widget_box")
             ).attr("id","split_1").css("min-width", 160).css("min-height", 100),
             ltk.VBox(
                 #ltk.HBox( 
                     # floats,fabric,instructions
                     svg_pattern_box
                 #).attr("id","renders")
             ).css("min-width", 80).css("min-height", 100).css("background", "lightyellow"),
            "main_splitter", self.calc_split_pos_1
        ).attr("id","splitter_1").css("width", "100%").css("height", "100vh")
        # splitter events
        # mousedown - register drag, calc offsets
        splitter = self.splitter.find(".ltk-horizontal-split-pane-middle:first")
        splitter.on(
            "mousedown", ltk.proxy(lambda event: start_splitmove(event)))
        splitter.on(
            "drag", ltk.proxy(lambda event, ui: shadow_splitmove(event,ui)))
        splitter.on(
            "mouseup", ltk.proxy(lambda event: end_splitmove(event)))
        # mouseup - deregister
        #
        return (
            ltk.VBox(ltk.Text("Tablet weaving Loom").addClass("title"),
                     ltk.TextArea("sh-L to add to selection. Resize using widget. W/H = mouse control").addClass("textbox"),
                     palette_box,
                     ltk.HBox(
                         ltk.VBox(
                             # palette, state, parts
                             colors_box, cell_box, size_box, parts_box
                         ).attr("id","side_menus"),
                         #
                         self.splitter,
                     ).attr("id","widgets")
            )
        )
        


# Main
if __name__ == "__main__":
    svg_dimensions = [800, 900] # calc to fil width of screen and exceed height by some amount ?
    initial_size = [16,8]
    initial_holecount = 4
    initial_ = 0
    tw = Tablet_weaver(initial_size[0], initial_size[1], initial_holecount)  # width, rpt_len, holes
    loom = Loom_widget(svg_dimensions, weaver=tw) #, cells=initial_size, holecount=initial_holecount)
    widget = loom.create()
    # only one of these on a page. id = "#tablet_loom"
    widget.appendTo(ltk.window.document.body)

#Notes:
# Custom svg cursor
#   - https://stackoverflow.com/questions/53285114/dynamically-change-svg-cursor
#   - https://blog.bradleygore.com/2017/01/02/dynamic-custom-svg-cursors/

# - Threaded in pattern browser - show lengths of connected variants based on blocks of F/W and rpt_length
#   - allow user to enter seq themselves. E.g. 4F,4B,2F,5B,..
# - Show refocusable box of:
#   - floats, back, rendered front with vertical rpts.
# mark segments and label so can combine in rendered rpts


# if click:
#   - if shift - add_selection(region,cell) - add add_targets() to this
#   - if ctrl - Store(region, cell, "alt_action")
#   - else    - Store(region, cell, "action")
# if mouseover:
#  - draw_highlight_over(region, cell) # and targets