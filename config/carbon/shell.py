#!/usr/bin/env python3
"""Carbon workstation: GTK/Wayland dashboard, volume meter and focus HUD."""
import calendar
import http.server
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import queue
import signal
import socket
import subprocess
import threading
import time
import gi
import cairo

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, Pango

ROOT = Path(__file__).resolve().parent
STATE = Path.home()/'.local/state/carbon'
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))/f'carbon-{os.getuid()}'
STATE.mkdir(parents=True, exist_ok=True)
RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
MONTHS = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
DAYS = ['seg','ter','qua','qui','sex','sáb','dom']

def run(*args):
    try: return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=2).strip()
    except (OSError, subprocess.SubprocessError): return ''

def launch(*args):
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

def box(vertical=False, gap=12, cls=None):
    w=Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL, spacing=gap)
    if cls: w.get_style_context().add_class(cls)
    return w

def add(parent, child, expand=False):
    parent.pack_start(child,expand,expand,0);return child

def label(text='', cls=None):
    w=Gtk.Label(label=text);w.set_xalign(0)
    if cls: w.get_style_context().add_class(cls)
    if cls in ('heading','brand'): w.set_halign(Gtk.Align.START);w.set_valign(Gtk.Align.CENTER)
    return w

def button(text, callback, cls=None):
    w=Gtk.Button(label=text);w.connect('clicked',lambda *_:callback())
    if cls: w.get_style_context().add_class(cls)
    return w

def card(title, cls=None):
    w=box(True,10,'card')
    if cls: w.get_style_context().add_class(cls)
    if title: add(w,label(title,'heading'))
    return w

def atomic(path, data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False));tmp.replace(path)

class Gauge(Gtk.DrawingArea):
    """Carbon meter: a flat 8px track on layer 02, filled in interactive blue, ten tick marks."""
    def __init__(self):
        super().__init__();self.value=0;self.set_size_request(288,12);self.connect('draw',self.draw)
    def draw(self,w,c):
        width=w.get_allocated_width()
        def color(h): c.set_source_rgb(*(int(h[i:i+2],16)/255 for i in (0,2,4)))
        color('393939');c.rectangle(0,0,width,8);c.fill()
        color('78A9FF');c.rectangle(0,0,width*self.value/100,8);c.fill()
        color('161616')
        for i in range(1,10): c.rectangle(round(width*i/10),0,1,8);c.fill()

class Shell:
    def __init__(self):
        self.windows={};self.metrics={};self.updating=queue.Queue();self.osd_timeout=0;self.tasks=[]
        tasks_path=STATE/'tasks.json'
        # Carry tasks and timer over from the previous themes on first start.
        for name in ('tasks.json','timer.json'):
            if (STATE/name).exists(): continue
            for theme in ('mainframe','neobrutal'):
                old=Path.home()/'.local/state'/theme/name
                if old.exists(): (STATE/name).write_bytes(old.read_bytes()); break
        try: self.tasks=json.loads(tasks_path.read_text())
        except (OSError,ValueError): pass
        self.mode='Foco';self.duration=25*60;self.remaining=self.duration;self.deadline=0;self.running=False;self.cycle=1
        try:
            data=json.loads((STATE/'timer.json').read_text())
            for k in ('mode','duration','remaining','deadline','running','cycle'): setattr(self,k,data[k])
        except (OSError,ValueError,KeyError): pass
        css=Gtk.CssProvider();css.load_from_path(str(ROOT/'style.css'))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_USER+1)
        self.make_dashboard();self.make_osd();self.make_hud();self.render_tasks()
        threading.Thread(target=self.poll,daemon=True).start()
        threading.Thread(target=self.serve_home,daemon=True).start()
        threading.Thread(target=self.listen,daemon=True).start()
        GLib.timeout_add_seconds(1,self.tick);self.tick()
    def serve_home(self):
        class HomeHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path not in ('/', '/home.html'):
                    self.send_error(404);return
                data=(ROOT/'home.html').read_bytes()
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
            def log_message(self,*args):pass
        try:http.server.ThreadingHTTPServer(('127.0.0.1',47831),HomeHandler).serve_forever()
        except OSError as e:print('Local home page:',e,flush=True)
    def window(self,name,content,width,height=-1,edges=(),keyboard=True,margins=None):
        w=Gtk.Window(title='Carbon · '+name);w.set_default_size(width,height);w.set_resizable(False)
        GtkLayerShell.init_for_window(w);GtkLayerShell.set_namespace(w,'carbon-'+name)
        GtkLayerShell.set_layer(w,GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(w,GtkLayerShell.KeyboardMode.ON_DEMAND if keyboard else GtkLayerShell.KeyboardMode.NONE)
        for edge in edges:
            GtkLayerShell.set_anchor(w,edge,True);GtkLayerShell.set_margin(w,edge,(margins or {}).get(edge,24))
        w.add(content);w.connect('key-press-event',lambda _,e:self.hide() if e.keyval==Gdk.KEY_Escape else False)
        self.windows[name]=w;w.show_all();w.hide();return w
    def hide(self):
        self.windows['dashboard'].hide();return True
    def listen(self):
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);path=RUNTIME/'shell.sock'
        path.unlink(missing_ok=True);sock.bind(str(path));os.chmod(path,0o600);sock.listen(4)
        while True:
            conn,_=sock.accept()
            with conn:
                conn.settimeout(2)
                try: data=json.loads(conn.recv(4096).decode());GLib.idle_add(self.command,data);conn.sendall(b'ok')
                except (ValueError,OSError): pass
    def command(self,data):
        cmd=data[0]
        if cmd in ('dashboard','widgets'):
            w=self.windows['dashboard'];w.hide() if w.get_visible() else w.show_all()
        elif cmd=='hide': self.hide()
        elif cmd=='osd': self.show_osd(data[1],float(data[2]),data[3] if len(data)>3 else '')
        elif cmd=='stop': self.save_timer();Gtk.main_quit()
        return False
    def make_dashboard(self):
        root=box(True,18,'surface');root.set_border_width(8)
        top=Gtk.Grid(column_spacing=22,row_spacing=22);top.set_column_homogeneous(True)
        clock=card(None,'clock-card');row=box()
        add(row,label('relógio','heading'),True);self.date=add(row,label('','muted'));self.date.set_halign(Gtk.Align.END);add(clock,row)
        self.clock=add(clock,label('','clock'),True)
        self.stats=add(clock,label('cpu …   mem …   up …','stats'))
        top.attach(clock,0,0,2,1)
        timer=card('timer','timer-card')
        self.timer_label=add(timer,label('25:00','timer'))
        self.progress=add(timer,Gtk.ProgressBar())
        self.timer_info=add(timer,label('foco · ciclo 1 de 4','muted'),True)
        row=box(False,6)
        for name,mins in [('Foco',25),('Pausa',5),('Longa',15)]: add(row,button(name,lambda n=name,m=mins:self.set_timer(n,m),'small'),True)
        add(timer,row);row=box(False,8)
        self.start_button=add(row,button('Iniciar',self.toggle_timer,'primary'),True)
        add(row,button('Zerar',lambda:self.set_timer(self.mode,self.duration//60),'secondary'),True);add(timer,row)
        top.attach(timer,2,0,1,1)
        media=card('mídia','media-card')
        self.cover=add(media,label('sem reprodução','cover'),True);self.cover.set_xalign(.5)
        self.track=add(media,label('Nenhuma faixa','song'));self.track.set_ellipsize(Pango.EllipsizeMode.END);self.track.set_max_width_chars(25)
        self.artist=add(media,label('Abra seu player','muted'));self.artist.set_ellipsize(Pango.EllipsizeMode.END);self.artist.set_max_width_chars(27)
        self.media_progress=add(media,Gtk.ProgressBar());row=box(False,8)
        for text,action in [('⏮','previous'),('Ⅱ','play-pause'),('⏭','next')]: add(row,button(text,lambda a=action:launch('playerctl',a),'ghost'),True)
        add(media,row);top.attach(media,3,0,1,1);add(root,top)
        bottom=Gtk.Grid(column_spacing=22);bottom.set_column_homogeneous(True)
        tasks=card(None);row=box();add(row,label('tarefas','heading'),True);self.task_count=add(row,label('','muted'));add(tasks,row)
        self.task_box=box(True,0);scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);scroll.set_min_content_height(215);scroll.add(self.task_box);add(tasks,scroll,True)
        add(tasks,label('nova tarefa','muted'));self.entry=Gtk.Entry();self.entry.set_placeholder_text('❯ escreva e tecle enter');self.entry.connect('activate',self.add_task);add(tasks,self.entry)
        bottom.attach(tasks,0,0,1,1)
        cal=card(None);row=box();add(row,label('calendário','heading'),True)
        add(row,button('‹',lambda:self.change_month(-1),'small'));self.month=add(row,label('','muted'));add(row,button('›',lambda:self.change_month(1),'small'));add(cal,row)
        now=dt.date.today();self.cal_year=now.year;self.cal_month=now.month
        self.cal_grid=Gtk.Grid(column_spacing=5,row_spacing=5);self.cal_grid.set_column_homogeneous(True);self.cal_grid.set_row_homogeneous(True);add(cal,self.cal_grid,True)
        self.cal_hint=add(cal,label('','muted'));self.render_calendar();bottom.attach(cal,1,0,1,1);add(root,bottom,True)
        footer=box(False,0,'footer');add(footer,label('carbon workstation','brand'));add(footer,Gtk.Box(),True)
        for text,cmd in [('Apps','launcher'),('Área de transferência','clipboard'),('Foco · F8','focus')]: add(footer,button(text,lambda c=cmd:(self.hide(),launch(str(ROOT/'control'),c)),'ghost'))
        add(footer,button('Fechar · esc',self.hide,'ghost'));add(root,footer)
        self.window('dashboard',root,1100,740)
    def render_calendar(self):
        for c in self.cal_grid.get_children():self.cal_grid.remove(c)
        self.month.set_text(f'{MONTHS[self.cal_month-1]} {self.cal_year}')
        for i,s in enumerate(['dom','seg','ter','qua','qui','sex','sáb']):
            w=label(s,'weekday');w.set_xalign(.5);self.cal_grid.attach(w,i,0,1,1)
        today=dt.date.today()
        for row,week in enumerate(calendar.Calendar(firstweekday=6).monthdayscalendar(self.cal_year,self.cal_month),1):
            for col,day in enumerate(week):
                w=label(f'{day:02}' if day else '','day' if day else 'empty-day');w.set_yalign(.2)
                if (self.cal_year,self.cal_month,day)==(today.year,today.month,today.day):w.get_style_context().add_class('today')
                self.cal_grid.attach(w,col,row,1,1)
        self.cal_hint.set_text(f'hoje · {DAYS[today.weekday()]} {today.day:02} de {MONTHS[today.month-1]}')
        self.cal_grid.show_all()
    def change_month(self,delta):
        index=self.cal_year*12+self.cal_month-1+delta;self.cal_year,self.cal_month=divmod(index,12);self.cal_month+=1;self.render_calendar()
    def add_task(self,entry):
        text=entry.get_text().strip()
        if text:self.tasks.append({'text':text,'done':False});self.save_tasks();entry.set_text('');self.render_tasks()
    def save_tasks(self):atomic(STATE/'tasks.json',self.tasks)
    def complete(self,i,done):self.tasks[i]['done']=done;self.save_tasks();self.render_tasks()
    def remove_task(self,i):self.tasks.pop(i);self.save_tasks();self.render_tasks()
    def render_tasks(self):
        for c in self.task_box.get_children():self.task_box.remove(c)
        self.task_count.set_text(f'{sum(bool(t.get("done")) for t in self.tasks)} / {len(self.tasks)}')
        if not self.tasks:add(self.task_box,label('Nenhuma tarefa. Escreva a próxima abaixo.','empty-tasks'))
        for i,t in enumerate(self.tasks):
            row=box(False,8,'task-row');w=Gtk.CheckButton();w.set_active(t.get('done',False));w.connect('toggled',lambda w,i=i:self.complete(i,w.get_active()));add(row,w)
            name=add(row,label(t['text'],'done' if t.get('done') else 'task-name'),True);name.set_ellipsize(Pango.EllipsizeMode.END);name.set_max_width_chars(38);name.set_tooltip_text(t['text'])
            delete=add(row,button('×',lambda i=i:self.remove_task(i),'delete'));delete.set_tooltip_text('Remover tarefa');add(self.task_box,row)
        self.task_box.show_all()
    def save_timer(self):atomic(STATE/'timer.json',{k:getattr(self,k) for k in ('mode','duration','remaining','deadline','running','cycle')})
    def set_timer(self,name,mins):self.mode=name;self.duration=mins*60;self.remaining=self.duration;self.running=False;self.save_timer();self.tick()
    def toggle_timer(self):
        if self.remaining<=0:self.remaining=self.duration
        if self.running:self.remaining=max(0,int(self.deadline-time.time()))
        else:self.deadline=time.time()+self.remaining
        self.running=not self.running;self.save_timer();self.tick()
    def make_osd(self):
        c=card(None,'osd');row=box();self.osd_heading=add(row,label('volume','heading'),True);self.osd_value=add(row,label('','osd-value'));add(c,row)
        self.gauge=add(c,Gauge());self.osd_note=add(c,label('alto-falantes','muted'))
        self.window('osd',c,320,-1,(GtkLayerShell.Edge.BOTTOM,),False,{GtkLayerShell.Edge.BOTTOM:48})
    def show_osd(self,kind,value,note):
        self.osd_heading.set_text(kind);self.gauge.value=max(0,min(100,value));self.gauge.queue_draw();self.osd_value.set_text(f'{round(value)}%');self.osd_note.set_text(note)
        self.windows['osd'].show_all()
        if self.osd_timeout:GLib.source_remove(self.osd_timeout)
        self.osd_timeout=GLib.timeout_add(1800,self.hide_osd)
    def hide_osd(self):self.windows['osd'].hide();self.osd_timeout=0;return False
    def make_hud(self):
        row=box(False,0,'focus-hud');add(row,label('foco','focus-tag'));self.hud_time=add(row,label('00:00','hud-time'));add(row,button('Sair · F8',lambda:launch(str(ROOT/'control'),'focus'),'ghost'))
        # Focus gaps are 60 with a 96 bottom strip (see control): align with the windows'
        # right edge and center the ~36px HUD in that strip, clear of the screen corner.
        self.window('hud',row,-1,-1,(GtkLayerShell.Edge.BOTTOM,GtkLayerShell.Edge.RIGHT),False,{GtkLayerShell.Edge.BOTTOM:30,GtkLayerShell.Edge.RIGHT:60})
    def poll(self):
        previous=None
        while True:
            try:
                nums=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]));total=sum(nums[:8]);idle=nums[3]+nums[4]
                cpu=0 if previous is None else 100*(1-(idle-previous[1])/max(1,total-previous[0]));previous=(total,idle)
                mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};used=(mem['MemTotal']-mem['MemAvailable'])/1048576
                up=int(float(Path('/proc/uptime').read_text().split()[0]));data={'cpu':round(cpu),'ram':f'{used:.1f}G','uptime':f'{up//3600}h{up//60%60:02}'}
                fields=run('playerctl','metadata','--format','{{title}}\t{{artist}}\t{{mpris:length}}\t{{status}}').split('\t')
                if len(fields)==4:data.update(zip(('title','artist','length','status'),fields));data['position']=run('playerctl','position')
                self.updating.put(data)
            except (OSError,ValueError): pass
            time.sleep(3)
    def tick(self):
        now=dt.datetime.now();self.clock.set_text(now.strftime('%H:%M'));self.date.set_text(f'{DAYS[now.weekday()]} {now.day:02} {MONTHS[now.month-1][:3]} {now.year}')
        if self.running:
            self.remaining=max(0,math.ceil(self.deadline-time.time()))
            if not self.remaining:
                self.running=False
                if self.mode=='Foco':self.cycle=self.cycle%4+1
                self.save_timer();launch('notify-send','Carbon · timer',self.mode+' concluído.')
        self.timer_label.set_text(f'{self.remaining//60:02}:{self.remaining%60:02}');self.progress.set_fraction(1-self.remaining/max(1,self.duration));self.timer_info.set_text(f'{self.mode.lower()} · ciclo {self.cycle} de 4');self.start_button.set_label('Pausar' if self.running else 'Iniciar')
        while not self.updating.empty():self.metrics=self.updating.get_nowait()
        m=self.metrics;self.stats.set_text(f'cpu {m.get("cpu","…")}%   mem {m.get("ram","…")}   up {m.get("uptime","…")}')
        self.track.set_text(m.get('title') or 'Nenhuma faixa');self.artist.set_text(m.get('artist') or 'Abra seu player');self.cover.set_text('reproduzindo' if m.get('status')=='Playing' else ('pausado' if m.get('title') else 'sem reprodução'))
        try:self.media_progress.set_fraction(max(0,min(1,float(m.get('position',0))*1000000/float(m.get('length',1)))))
        except (ValueError,ZeroDivisionError):self.media_progress.set_fraction(0)
        focus=RUNTIME/'focus.json'
        if focus.exists():
            try:
                data=json.loads(focus.read_text());seconds=max(0,int(time.time()-data['started']));self.hud_time.set_text(f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}');self.windows['hud'].show_all()
            except (OSError,ValueError,KeyError):pass
        else:self.windows['hud'].hide()
        return True

if __name__=='__main__':
    lock=open(RUNTIME/'shell.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit(0)
    app=Shell()
    def stop(*_):GLib.idle_add(lambda:(app.save_timer(),Gtk.main_quit(),False)[-1])
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    Gtk.main()
