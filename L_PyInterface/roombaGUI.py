'''
roombaGUI.py
@author: River Allen
@date: July 13, 2010

'''

import pygtk
import cairo
import gtk
import gobject
import threading

class RoombaLocalizationGUI(threading.Thread):
    def delete_event(self, widget, data=None):
        print 'Exit GUI!'
        self.quit = True
        return False

    def destroy(self, widget, data=None):
        self.quit = True
        gtk.main_quit()
    
    def _update_clock(self):
        self.window.queue_draw()
        return True
    
    def __init__(self, filter_draw_methods={}, map_obj=None):
        threading.Thread.__init__(self)
        self.quit = False
        self.init_pos = [50, 475]
        self.transform_mat = cairo.Matrix(1.5, 0, 0, -1.5, self.init_pos[0], self.init_pos[1])
        
        self._filter_draw_methods = filter_draw_methods
        self._draw_methods = []
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        
        self.window.connect('delete_event', self.delete_event)
        self.window.connect('destroy', self.destroy)
        self.window.set_title('Roomba Localization')
        self.window.set_size_request(500, 600)

        self.area = gtk.DrawingArea()
        self.area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        
        self.area.connect("expose-event", self._expose_cb)
        self.area.connect('button_press_event', self._click_cb)


        #===============================================================================
        # Map 
        #===============================================================================
        if map_obj is None:
            import Map
            self.map_obj = Map.GridMap()
        else:
            self.map_obj = map_obj
        self.map_frame = gtk.Frame('Map')
        self.map_frame.add(self.area)
        #------------------------------------------------------------------------------ 
        #self.window.add(self.area)
        self.window.add(self.map_frame)
        self.window.show_all()
        
        self._click_positions = []
        
        gobject.timeout_add(500, self._update_clock)
    
    def add_draw_method(self, meth):
        self._draw_methods.append(meth)
        
    def add_filter_draw_method(self, meth):
        print self._filter_draw_methods
        print meth
        self._filter_draw_methods.update(meth)
    
    def _click_cb(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.transform(self.transform_mat)
        #print 'Device Click Coords', event.get_coords()
        self._click_positions.append(cr.device_to_user(*event.get_coords()))
        #print 'Local Click Coords', self._click_positions
        #print self.click_positions
        
    def _expose_cb(self, widget, event):
        
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        #cr.translate(*self.init_pos)
        #cr.scale(1.5, 1.5)
        cr.transform(self.transform_mat)
        #cr.paint()
        
        self.map_obj.draw(cr)
        
        for draw_meth in self._draw_methods:
            draw_meth(cr)
        
        for draw_meth in self._filter_draw_methods.values():
            draw_meth(cr)
        
    def _draw_map(self, cr):
        # Draw grid
        grid_lims = [200, 300]
        box_size = 25
        
        cr.set_source_rgba(0.7, 1.0, 0.3, 0.5)
        #cr.arc(50, 50, 10, 0, 2*3.1415)
        
        for x in range(grid_lims[0]/box_size):
            for y in range(grid_lims[1]/box_size):
                cr.rectangle(x * box_size, y * box_size, box_size, box_size)
        
        #cr.fill()
        cr.stroke()
        
    def get_click_positions(self):
        ret_pos = self._click_positions
        self._click_positions = []
        return ret_pos
    
    def mainloop(self):
        gobject.timeout_add (100, self.check)
        gtk.main()

    def check(self):
        if self.quit:
            self.destroy(None)
        
    
    run = mainloop










'''
import pygtk
pygtk.require('2.0')
import gtk
import numpy as np
import threading
import gobject
import time

class RoombaLocalizationGUI():

    def delete_event(self, widget, data=None):
        print 'Exit...'
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    
    def __init__(self):
        self.grid_lims = [200,300]
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        
        self.window.connect('delete_event', self.delete_event)
        self.window.connect('destroy', self.destroy)
        self.window.set_title('Roomba Localization')
        self.window.set_size_request(500, 400)
        
        self.area = gtk.DrawingArea()
        self.area.connect("expose-event", self.area_expose_cb)
        #self.area.connect('button_press_event', self.area_click_cb)
        
        self.pangolayout = self.area.create_pango_layout("")
        
        self.map_frame = gtk.Frame()
        self.map_frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        #self.map_frame.connect('button_press_event', self.area_click_cb)
        self.map_frame.add(self.area)
        
        self.filter_frame = gtk.Frame()
        self.filter_frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        
        self.table = gtk.Table(3, 2)
        self.table.attach(self.map_frame, 0, 1, 0, 3)
        self.table.attach(self.filter_frame, 1, 2, 0, 2)
        #self.table.connect_object('button_press_event', self.area_click_cb, self.map_frame)
        self.window.connect('button_press_event', self.area_click_cb)
        
        self.area.set_size_request(400, 300)
        self.window.add(self.table)
        self.area.show()
        self.map_frame.show()
        self.table.show()
        self.window.show()
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        
        
        self.show_filters = {'particleFilter':True}
        self.filters = []
        
        self.explorer_pos = np.array([100,150,0]) 
        #self.draw_map()
        

    def area_expose_cb(self, area, event):
        self.redraw()
        return True
    
    def area_click_cb(self, widget, event, data=None):
        #print dir(event)
        print event.get_coords()
        x, y = event.get_coords()
        width = height = 5
        self.area.window.draw_arc(self.gc, False, x-width/2., y-height/2., width, height,
                                  angle1=0, angle2=360*100)

    def redraw(self):
        self.area.window.clear()
        self.draw_map()
        for filt in self.filters:
            pass
            #if self.show_filters[filt.name]:
                # filt.draw_explorer
                # filt.draw_heading
        
        # Temp
        self.draw_explorer()
        
    def draw_map(self):
        
        box_size = 25
        
        def draw_grid_box(x, y, width=25, height=25):
            self.area.window.draw_rectangle(self.gc, False, x, y, width, height)
        
        self.init_x_pos = 100
        self.init_y_pos = 50
        for x in range(self.grid_lims[0]/box_size):
            for y in range(self.grid_lims[1]/box_size):
                draw_grid_box(self.init_x_pos + x*box_size, self.init_y_pos + y*box_size, box_size, box_size)
        self.pangolayout.set_text("(0, 0)")
        self.area.window.draw_layout(self.gc, self.init_x_pos - 20, self.init_y_pos + self.grid_lims[1] + 2, self.pangolayout)
        self.pangolayout.set_text("(200, 300)")
        self.area.window.draw_layout(self.gc, self.init_x_pos - 30 + self.grid_lims[0], self.init_y_pos - 15, self.pangolayout)

    def draw_explorer(self):
        roomba_rad = 16.75 * 2
        x = self.explorer_pos[0] + self.init_x_pos
        y = self.explorer_pos[1] + self.init_y_pos
        self.area.window.draw_arc(self.gc, False, x-roomba_rad/2., y-roomba_rad/2., roomba_rad, roomba_rad,
                                  angle1=0, angle2=360*100)

    def main(self):
        gtk.main()
        

class changeGUIData(threading.Thread):
    def __init__(self, explorer_pos, redraw):
        threading.Thread.__init__(self)
        
        self.explorer_pos = explorer_pos
        self.redraw = redraw
        self.quit = False
        
    def run(self):
        for i in range(1000):
            if self.quit:
                return
            if self.explorer_pos[0] >= 200:
                self.explorer_pos[0] = 0
            self.explorer_pos[0] += 10
            self.redraw()
            time.sleep(0.5)

if __name__ == '__main__':
    # Test Gui
    base = RoombaLocalizationGUI()
    chgGUI = changeGUIData(base.explorer_pos, base.redraw)
    
    # Need to call this or gtk will never release locks
    gobject.threads_init()

    chgGUI.start()
    
    base.main()
    chgGUI.quit = True

'''
'''
# example drawingarea.py

import pygtk
pygtk.require('2.0')
import gtk
import operator
import time
import string

class DrawingAreaExample:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Drawing Area Example")
        window.connect("destroy", lambda w: gtk.main_quit())
        self.area = gtk.DrawingArea()
        self.area.set_size_request(400, 300)
        self.pangolayout = self.area.create_pango_layout("")
        self.sw = gtk.ScrolledWindow()
        self.sw.add_with_viewport(self.area)
        self.table = gtk.Table(2,2)
        self.hruler = gtk.HRuler()
        self.vruler = gtk.VRuler()
        self.hruler.set_range(0, 400, 0, 400)
        self.vruler.set_range(0, 300, 0, 300)
        self.table.attach(self.hruler, 1, 2, 0, 1, yoptions=0)
        self.table.attach(self.vruler, 0, 1, 1, 2, xoptions=0)
        self.table.attach(self.sw, 1, 2, 1, 2)
        window.add(self.table)
        self.area.set_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        self.area.connect("expose-event", self.area_expose_cb)
        def motion_notify(ruler, event):
            return ruler.emit("motion_notify_event", event)
        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.hruler)
        self.area.connect_object("motion_notify_event", motion_notify,
                                 self.vruler)
        self.hadj = self.sw.get_hadjustment()
        self.vadj = self.sw.get_vadjustment()
        def val_cb(adj, ruler, horiz):
            if horiz:
                span = self.sw.get_allocation()[3]
            else:
                span = self.sw.get_allocation()[2]
            l,u,p,m = ruler.get_range()
            v = adj.value
            ruler.set_range(v, v+span, p, m)
            while gtk.events_pending():
                gtk.main_iteration()
        self.hadj.connect('value-changed', val_cb, self.hruler, True)
        self.vadj.connect('value-changed', val_cb, self.vruler, False)
        def size_allocate_cb(wid, allocation):
            x, y, w, h = allocation
            l,u,p,m = self.hruler.get_range()
            m = max(m, w)
            self.hruler.set_range(l, l+w, p, m)
            l,u,p,m = self.vruler.get_range()
            m = max(m, h)
            self.vruler.set_range(l, l+h, p, m)
        self.sw.connect('size-allocate', size_allocate_cb)
        self.area.show()
        self.hruler.show()
        self.vruler.show()
        self.sw.show()
        self.table.show()
        window.show()

    def area_expose_cb(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        self.draw_point(10,10)
        self.draw_points(110, 10)
        self.draw_line(210, 10)
        self.draw_lines(310, 10)
        self.draw_segments(10, 100)
        self.draw_rectangles(110, 100)
        self.draw_arcs(210, 100)
        self.draw_pixmap(310, 100)
        self.draw_polygon(10, 200)
        self.draw_rgb_image(110, 200)
        return True

    def draw_point(self, x, y):
        self.area.window.draw_point(self.gc, x+30, y+30)
        self.pangolayout.set_text("Point")
        self.area.window.draw_layout(self.gc, x+5, y+50, self.pangolayout)
        return

    def draw_points(self, x, y):
        points = [(x+10,y+10), (x+10,y), (x+40,y+30),
                  (x+30,y+10), (x+50,y+10)]
        self.area.window.draw_points(self.gc, points)
        self.pangolayout.set_text("Points")
        self.area.window.draw_layout(self.gc, x+5, y+50, self.pangolayout)
        return

    def draw_line(self, x, y):
        self.area.window.draw_line(self.gc, x+10, y+10, x+20, y+30)
        self.pangolayout.set_text("Line")
        self.area.window.draw_layout(self.gc, x+5, y+50, self.pangolayout)
        return

    def draw_lines(self, x, y):
        points = [(x+10,y+10), (x+10,y), (x+40,y+30),
                  (x+30,y+10), (x+50,y+10)]
        self.area.window.draw_lines(self.gc, points)
        self.pangolayout.set_text("Lines")
        self.area.window.draw_layout(self.gc, x+5, y+50, self.pangolayout)
        return

    def draw_segments(self, x, y):
        segments = ((x+20,y+10, x+20,y+70), (x+60,y+10, x+60,y+70),
            (x+10,y+30 , x+70,y+30), (x+10, y+50 , x+70, y+50))
        self.area.window.draw_segments(self.gc, segments)
        self.pangolayout.set_text("Segments")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

    def draw_rectangles(self, x, y):
        self.area.window.draw_rectangle(self.gc, False, x, y, 80, 70)
        self.area.window.draw_rectangle(self.gc, True, x+10, y+10, 20, 20)
        self.area.window.draw_rectangle(self.gc, True, x+50, y+10, 20, 20)
        self.area.window.draw_rectangle(self.gc, True, x+20, y+50, 40, 10)
        self.pangolayout.set_text("Rectangles")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

    def draw_arcs(self, x, y):
        self.area.window.draw_arc(self.gc, False, x+10, y, 70, 70,
                                  0, 360*64)
        self.area.window.draw_arc(self.gc, True, x+30, y+20, 10, 10,
                                  0, 360*64)
        self.area.window.draw_arc(self.gc, True, x+50, y+20, 10, 10,
                                  0, 360*64)
        self.area.window.draw_arc(self.gc, True, x+30, y+10, 30, 50,
                                  210*64, 120*64)
        self.pangolayout.set_text("Arcs")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

    def draw_pixmap(self, x, y):
        pixmap, mask = gtk.gdk.pixmap_create_from_xpm(
            self.area.window, self.style.bg[gtk.STATE_NORMAL], "gtk.xpm")

        self.area.window.draw_drawable(self.gc, pixmap, 0, 0, x+15, y+25,
                                       -1, -1)
        self.pangolayout.set_text("Pixmap")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

    def draw_polygon(self, x, y):
        points = [(x+10,y+60), (x+10,y+20), (x+40,y+70),
                  (x+30,y+30), (x+50,y+40)]
        self.area.window.draw_polygon(self.gc, True, points)
        self.pangolayout.set_text("Polygon")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

    def draw_rgb_image(self, x, y):
        b = 80*3*80*['\0']
        for i in range(80):
            for j in range(80):
                b[3*80*i+3*j] = chr(255-3*i)
                b[3*80*i+3*j+1] = chr(255-3*abs(i-j))
                b[3*80*i+3*j+2] = chr(255-3*j)
        buff = string.join(b, '')
        self.area.window.draw_rgb_image(self.gc, x, y, 80, 80,
                                 gtk.gdk.RGB_DITHER_NONE, buff, 80*3)
        self.pangolayout.set_text("RGB Image")
        self.area.window.draw_layout(self.gc, x+5, y+80, self.pangolayout)
        return

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    DrawingAreaExample()
    main()
'''
    