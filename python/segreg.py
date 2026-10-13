#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEGREG - Python/Tkinter translation of segreg.prg
(Dr. R. Beunis, Visual FoxPro 9.0, version 03/02/2020)

Simulates how two conditioned stimuli (CS1, a 'tone' with an ISI of 800 ms, and
CS2, a 'light' with an ISI of 400 ms) that compete for the same nanoloops in the
nucleus interpositus segregate onto different nanoloops, and how the transient
'double peaks phenomenon' appears on the way, as described in Beunis R. (2021)
"An Eye Blink Reflex Model based on an Intracellular Timing Mechanism in Purkinje
Cells and on a Conditioned Stimulus Segregation Mechanism in the Nucleus
Interpositus might explain the Double Peaks Phenomenon", Zenodo,
doi:10.5281/zenodo.17584844.

The translation follows segreg.prg procedure by procedure (same names: DEMO,
SETTINGS, LOADSPS, DORUN, CSALL, LTPD, SUM_SS, SUM_SSCR, DEL_TERM, ADD_TERM,
LINEDRAW, GAUSS).  The VFP form is emulated with a raster image (Pillow) on
which drawing uses the same 'form graphics' state as VFP (ForeColor, FillColor,
FillStyle, DrawWidth, DrawStyle, Line, Circle, PSet, Print, Cls), with Tk
controls at the same pixel positions as the VFP objects.

The program follows the version in which the screenshots and videos of the
article were made (the SEGREG form built into the author's article reader):
the switch is called 'BEAM' (not 'BACKGROUND'), the STOP button is always
shown, the form width pnW is 1264, and the demos show the same controls.

Deliberate differences from VFP:
  * RAND() -> Python random.  Reproducing the exact random sequence of a VFP
    run is impossible; with --seed a run is reproducible.
  * The speed of a step is taken from VFP 9 (measured: about 0.2 ms + 0.28 ms
    per NON, i.e. 170 steps/s with 20 NONs); a playback speed control and a
    demo panel were added.
  * The parameter table SEGREGMEM.DBF is not kept between sessions: the
    program starts with the demo values.
  * The form widens to the right when the trace needs more room (in VFP its
    left edge moved to the left).

Usage:
  python segreg.py                 normal mode
  python segreg.py --demo 7        demo mode (pcCMD = "1".."14")
  python segreg.py --speed 0.5     half speed
  python segreg.py --seed 123      reproducible run
"""

import argparse
import math
import random
import re
import sys
import time
import tkinter as tk
import tkinter.font as tkfont

from PIL import Image, ImageDraw, ImageFont, ImageTk

# ----------------------------------------------------------------------------
# Colours (PROCEDURE INITCOLOR)
# ----------------------------------------------------------------------------
pnZwart = (0, 0, 0)
pnGrijs = (128, 128, 128)
pnWit = (255, 255, 255)
pnRood = (255, 0, 0)
pnBlauw = (0, 0, 255)
pnGeel = (255, 255, 0)
pnCyaan = (0, 255, 255)

LABEL_BACK = (225, 225, 225)
pcCR = "\n"                     # CHR(13)
PNW, PNH = 1264, 540           # pnW = 1264 as in the article version of the program; pnH = form height
PANEL_W = 160                  # demo panel to the right of the form


def hexc(c):
    return "#%02x%02x%02x" % c


# ----------------------------------------------------------------------------
# VFP helper functions
# ----------------------------------------------------------------------------
def INT(x):
    """INT(): truncation (CHR() of a fractional number also truncates, measured in VFP 9)."""
    return math.trunc(x)


def isfinite(*xs):
    return all(math.isfinite(x) for x in xs)


def div(a, b):
    """Division as in VFP: a division by zero does not stop the program but gives an
    overflow value (printed as asterisks).  NaN plays that role here."""
    try:
        return a / b
    except ZeroDivisionError:
        return math.nan if a == 0 else math.copysign(math.inf, a)


def RGB(r, g, b):
    """RGB() of an overflow value returns 0 (measured in VFP 9)."""
    if not isfinite(r, g, b):
        return 0
    return ((INT(r) & 255) << 16) | ((INT(g) & 255) << 8) | (INT(b) & 255)


def rgb_tuple(c):
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


def STR(n, length=10, dec=0):
    """VFP STR(): right-aligned, rounded half away from zero, decimals dropped when the
    number does not fit; an overflow value prints as asterisks.  Decimal separator ','
    as on the screenshots in the article."""
    if not math.isfinite(n):
        return "*" * length
    for d in range(dec, -1, -1):
        f = 10 ** d
        r = math.floor(abs(n) * f + 0.5 + 1e-7) / f
        s = ("-" if n < 0 and r != 0 else "") + "%.*f" % (d, r)
        if len(s) <= length:
            return s.rjust(length).replace(".", ",")
    return "*" * length


def LTSTR(n):
    """LTRIM(STR(n))"""
    return str(int(round(n)))


def STREXTRACT(s, delim, n):
    parts = s.split(delim)
    return parts[n] if n < len(parts) else ""


_WORDS = re.compile(r"\S+")


class Stopped(Exception):
    """The form is replaced (another demo chosen) or the window is closed."""


# ----------------------------------------------------------------------------
# Form graphics (VFP Form.Line/Circle/PSet/Print/Cls on a raster image)
# ----------------------------------------------------------------------------
class FormGraphics:
    FONTFILES = {("Arial", True): "arialbd.ttf", ("Courier New", True): "courbd.ttf"}

    def __init__(self, w, h, back):
        self.W, self.H = int(w), int(h)
        self.BackColor = back
        self.img = Image.new("RGB", (self.W, self.H), back)
        self.d = ImageDraw.Draw(self.img)
        self.px = self.img.load()
        self.ForeColor = pnZwart
        self.FillColor = pnZwart
        self.FillStyle = 1
        self.DrawWidth = 1
        self.DrawStyle = 0
        self.FontSize = 6
        self.FontName = "Courier New"
        self._fonts = {}
        self._textcache = {}
        self.dirty = True

    def font(self):
        key = (self.FontName, self.FontSize)
        if key not in self._fonts:
            fn = self.FONTFILES.get((self.FontName, True), "courbd.ttf")
            px = int(self.FontSize * 96 / 72 + 0.5)      # MulDiv(pt, 96, 72)
            for name in (fn, "C:/Windows/Fonts/" + fn, "DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf"):
                try:
                    self._fonts[key] = ImageFont.truetype(name, px)
                    break
                except OSError:
                    continue
            else:
                self._fonts[key] = ImageFont.load_default()
        return self._fonts[key]

    def Cls(self):
        self.d.rectangle([0, 0, self.W, self.H], fill=self.BackColor)
        self.dirty = True

    def Line(self, x1, y1, x2, y2):
        if not math.isfinite(x1 + y1 + x2 + y2):   # overflow coordinates: nothing is drawn
            return
        w = max(1, int(self.DrawWidth))
        p1 = (int(round(x1)), int(round(y1)))
        p2 = (int(round(x2)), int(round(y2)))
        if w == 1 and self.DrawStyle == 2:     # dot: 3 pixels on, 3 off (GDI cosmetic PS_DOT pen)
            self._dotted(p1, p2)
        else:
            self.d.line([p1, p2], fill=self.ForeColor, width=w)
            if w > 2:   # GDI pens have round end caps
                r = (w - 1) / 2
                for (x, y) in (p1, p2):
                    self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.ForeColor)
        self.dirty = True

    def _dotted(self, p1, p2):
        (x1, y1), (x2, y2) = p1, p2
        dx, sx = abs(x2 - x1), (1 if x1 < x2 else -1)
        dy, sy = -abs(y2 - y1), (1 if y1 < y2 else -1)
        err, k, c, px = dx + dy, 0, self.ForeColor, self.px
        while True:
            if k % 6 < 3 and 0 <= x1 < self.W and 0 <= y1 < self.H:
                px[x1, y1] = c
            k += 1
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def PSet(self, x, y):
        if not math.isfinite(x + y):
            return
        x, y = int(round(x)), int(round(y))
        w = max(1, int(self.DrawWidth))
        if w == 1:
            if 0 <= x < self.W and 0 <= y < self.H:
                self.px[x, y] = self.ForeColor
        else:
            r = (w - 1) / 2
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.ForeColor)
        self.dirty = True

    def Circle(self, r, x, y):
        if not math.isfinite(x + y):
            return
        x, y = int(round(x)), int(round(y))
        w = max(1, int(self.DrawWidth))
        e = w // 2
        box = [x - r - e, y - r - e, x + r + e, y + r + e]
        fill = self.FillColor if self.FillStyle == 0 else None
        self.d.ellipse(box, fill=fill, outline=self.ForeColor, width=w)
        self.dirty = True

    def Print(self, t, x, y):
        # Opaque text (FontTransparent = .F.), as on the screenshots.  The form font is monospaced:
        # the background of the whole string is filled, and the words are pasted from a cache of
        # rendered snippets (much faster than rendering every changing number string anew).
        f = self.font()
        adv = f.getlength("0")
        asc, desc = f.getmetrics()
        x, y = int(round(x)), int(round(y))
        self.d.rectangle([x, y, x + int(adv * len(t)), y + asc + desc - 1], fill=self.BackColor)
        for m in _WORDS.finditer(t):
            w = m.group()
            key = (w, self.FontName, self.FontSize, self.ForeColor, self.BackColor)
            tile = self._textcache.get(key)
            if tile is None:
                tile = Image.new("RGB", (int(f.getlength(w)) + 1, asc + desc), self.BackColor)
                ImageDraw.Draw(tile).text((0, 0), w, font=f, fill=self.ForeColor, anchor="la")
                if len(self._textcache) > 50000:
                    self._textcache.clear()
                self._textcache[key] = tile
            self.img.paste(tile, (x + int(round(m.start() * adv)), y))
        self.dirty = True


# ----------------------------------------------------------------------------
# Controls
# ----------------------------------------------------------------------------
class ToolTip:
    def __init__(self, ctl):
        self.ctl = ctl
        self.tip = None
        self.job = None
        for w in ctl.all_widgets():
            w.bind("<Enter>", self.enter, add="+")
            w.bind("<Leave>", self.leave, add="+")
            w.bind("<ButtonPress>", self.leave, add="+")

    def enter(self, _e=None):
        self.cancel()
        self.job = self.ctl.app.root.after(500, self.show)

    def cancel(self):
        if self.job:
            try:
                self.ctl.app.root.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def show(self):
        self.job = None
        text = self.ctl.ToolTipText
        if not text:
            return
        root = self.ctl.app.root
        x, y = root.winfo_pointerx() + 12, root.winfo_pointery() + 18
        self.tip = tk.Toplevel(root)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=text, justify="left", bg="#ffffe1", relief="solid",
                 bd=1, font=self.ctl.app.tkfont("Arial", 8, False),
                 wraplength=500).pack()
        self.tip.wm_geometry("+%d+%d" % (x, y))

    def leave(self, _e=None):
        self.cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


class Ctl:
    """Common VFP properties: Name, Visible, Enabled, ToolTipText, Tag, position."""
    cls = ""

    def __init__(self, app, name, widget):
        self.app = app
        self.Name = name
        self.w = widget
        self._visible = True
        self._enabled = True
        self.ToolTipText = ""
        self.Tag = ""
        self.geom = (0, 0, 0, 0)
        ToolTip(self)

    def all_widgets(self):
        return [self.w]

    def place(self, left, top, width, height):
        self.geom = (left, top, width, height)
        self._place()

    def _place(self):
        S = self.app.S
        l, t, w, h = self.geom
        if self._visible:
            x0, x1 = int(round(l * S)), int(round((l + w) * S))
            y0, y1 = int(round(t * S)), int(round((t + h) * S))
            self.w.place(x=x0, y=y0, width=x1 - x0, height=y1 - y0)
        else:
            self.w.place_forget()

    @property
    def Visible(self):
        return self._visible

    @Visible.setter
    def Visible(self, v):
        self._visible = bool(v)
        self._place()

    @property
    def Enabled(self):
        return self._enabled

    @Enabled.setter
    def Enabled(self, v):
        self._enabled = bool(v)
        self._apply()

    def _apply(self):
        pass


class VLabel(Ctl):
    """VFP LABEL with BorderStyle = 1 and Alignment = 2 (centred)."""

    def __init__(self, app, name, cls, caption="", fontsize=8, fore=pnZwart, back=pnWit):
        lbl = tk.Label(app.root, bd=0, anchor="n", justify="center", padx=0, pady=1,
                       highlightthickness=1, highlightbackground="black", highlightcolor="black")
        self.cls = cls
        self._caption = caption
        self._fore = fore
        self._back = back
        self._fontsize = fontsize
        super().__init__(app, name, lbl)
        self._apply()

    def _flush(self):
        self.w.config(text=self._caption)

    @property
    def Caption(self):
        return self._caption

    @Caption.setter
    def Caption(self, v):
        # As in VFP: a new caption only appears at the next repaint.
        if v != self._caption:
            self._caption = v
            self.app._dirty_labels.add(self)

    @property
    def ForeColor(self):
        return self._fore

    @ForeColor.setter
    def ForeColor(self, v):
        self._fore = v
        self._apply()

    @property
    def BackColor(self):
        return self._back

    @BackColor.setter
    def BackColor(self, v):
        self._back = v
        self._apply()

    def _apply(self):
        fg = self._fore if self._enabled else (109, 109, 109)
        self.w.config(text=self._caption, fg=hexc(fg), bg=hexc(self._back),
                      font=self.app.tkfont("Arial", self._fontsize, True))


class VButton(Ctl):
    """VFP COMMANDBUTTON (here only used as a caption above a spinner)."""

    def __init__(self, app, name, cls, caption="", fontsize=6):
        b = tk.Button(app.root, text=caption, takefocus=0, padx=0, pady=0, bd=1,
                      font=app.tkfont("Arial", fontsize, True), bg=hexc(LABEL_BACK))
        self.cls = cls
        self.Caption = caption
        super().__init__(app, name, b)

    def _apply(self):
        self.w.config(state="normal" if self._enabled else "disabled")

    def place(self, left, top, width, height):
        super().place(left, top, width, height)
        self.w.config(wraplength=int((width - 2) * self.app.S))


class VSpinner(Ctl):
    """VFP SPINNER: text box with arrows, value shown with a decimal comma."""

    def __init__(self, app, name, low, high, inc, value):
        f = tk.Frame(app.root, bd=1, relief="sunken", bg="white")
        self.cls = "SG_SP"
        self.SpinnerLowValue = low
        self.SpinnerHighValue = high
        self.Increment = inc
        self._value = value
        self.on_user = None          # InteractiveChange / Valid: the user changed the value
        fnt = app.tkfont("Arial", 7, True)
        self.entry = tk.Entry(f, justify="right", bd=0, font=fnt,
                              disabledbackground="#f0f0f0", disabledforeground="#a0a0a0")
        bf = tk.Frame(f, bg="white")
        afont = app.tkfont("Arial", 5, True)
        self.up = tk.Button(bf, text="\u25b2", font=afont, padx=0, pady=0, bd=1,
                            takefocus=0, command=lambda: self.spin(+1))
        self.dn = tk.Button(bf, text="\u25bc", font=afont, padx=0, pady=0, bd=1,
                            takefocus=0, command=lambda: self.spin(-1))
        self.up.place(relx=0, rely=0, relwidth=1, relheight=0.5)
        self.dn.place(relx=0, rely=0.5, relwidth=1, relheight=0.5)
        self.entry.place(x=0, y=0, relwidth=1, width=-int(17 * app.S), relheight=1)
        bf.place(relx=1, x=-int(16 * app.S), y=0, width=int(16 * app.S), relheight=1)
        self.entry.bind("<FocusOut>", self._parse)
        self.entry.bind("<Return>", self._parse)
        super().__init__(app, name, f)
        self._show()

    def all_widgets(self):
        return [self.w, self.entry, self.up, self.dn]

    def _fmt(self, v):
        if float(self.Increment).is_integer() and float(v).is_integer():
            return str(int(v))
        s = ("%.4f" % v).rstrip("0")
        if s.endswith("."):
            s += "0"
        return s.replace(".", ",")

    def _show(self):
        st = self.entry.cget("state")
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, self._fmt(self._value))
        self.entry.config(state=st)

    def _parse(self, _e=None):
        try:
            v = float(self.entry.get().replace(",", "."))
        except ValueError:
            self._show()
            return
        old = self._value
        self.Value = v
        if self._value != old and self.on_user:
            self.on_user(0)

    def spin(self, d):
        if self._enabled:
            self.Value = round(self._value + d * self.Increment, 10)
            if self.on_user:
                self.on_user(d)

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, v):
        # Setting Value in code does not write to the ControlSource (as in VFP); only user changes do.
        v = min(max(v, self.SpinnerLowValue), self.SpinnerHighValue)
        if float(self.Increment).is_integer() and float(v).is_integer():
            v = int(v)
        self._value = v
        self._show()

    def _apply(self):
        st = "normal" if self._enabled else "disabled"
        self.entry.config(state=st)
        self.up.config(state=st)
        self.dn.config(state=st)


# ----------------------------------------------------------------------------
# The SEGREG form
# ----------------------------------------------------------------------------
# SEGREGMEM.DBF: one record with the parameters (FIELD(1)..FIELD(9) are the ControlSources of SG_SP1..9)
FIELDS = ["NONQTY", "LTP", "LTD", "CR_TH", "LTP_BR_TH", "RAND", "BGN", "INICHANCE", "STOPLIM"]
DEMO_SGM = dict(NONQTY=20, LTP=1.0, LTD=0.1, CR_TH=30, LTP_BR_TH=70, RAND=1, BGN=0, INICHANCE=1, STOPLIM=90)


class SGMRecord:
    """The current record of SEGREGMEM.DBF (alias SGM)."""

    def __init__(self):
        self.__dict__.update(DEMO_SGM)

    def replace(self, **kw):
        self.__dict__.update(kw)


class Segreg:

    def __init__(self, root, S, plCalled=False, pcCMD="", plIA=False, seed=None):
        self.root = root
        self.S = S
        self.closed = False
        self.dead = False
        self.running = False
        self.busy = 0                 # >0 while activate/DEMO/a click is still on the call stack
        self._keys = 0
        self._tkfonts = {}
        self._dirty_labels = set()
        self.speed = 1.0              # playback speed (set in the demo panel)
        self.on_width = None
        self._due = self._last_ev = time.perf_counter()

        self.rng = random.Random(seed) if seed is not None else random.Random()

        # PUBLIC variables
        self.plCalled = plCalled
        self.pcCMD = pcCMD
        self.plIA = plIA
        self.plStop = self.plRun = self.plAbort = False
        self.pnW, self.pnH = PNW, PNH
        self.pnDist = self.pnHOffSet = self.pnVOffSet = self.pnHPosNON = self.pnHPosPuC = self.pnRad = 0
        self.pnSteps = self.pnStepsTot = self.pnSUMSS_BUS = self.pnSUMSS_EUS = self.pnSatELTP = self.pnStepFactor = 0
        self.pnSatBLTP = 0

        # SEGREGMEM.DBF is not kept between sessions here: the record starts with the demo values.
        self.SGM = SGMRecord()
        self.SS = [None, [0.0], [0.0]]
        self.SUMSS = [0.0, 0.0, 0.0]
        self.SUMSSCR1 = [0.0, 0.0, 0.0]
        self.SUMSSCR2 = [0.0, 0.0, 0.0]
        self.TERMS = [None, [], []]

        # The form itself (BackColor = pnWit)
        self.g = FormGraphics(self.pnW, self.pnH, pnWit)
        self._width = int(self.pnW / 2)
        self.bg_label = tk.Label(root, bd=0, highlightthickness=0, bg=hexc(pnWit), anchor="nw")
        self.bg_label.place(x=0, y=0)
        self.tkimg = None
        self.refresh()
        self._autorefresh()

        root.bind_all("<Key>", self._key)
        self.controls = {}
        self.build()

    # -- infrastructure ------------------------------------------------------
    def tkfont(self, name, pt, bold):
        key = (name, pt, bold)
        if key not in self._tkfonts:
            self._tkfonts[key] = tkfont.Font(
                root=self.root, family=name,
                size=-int(pt * 96 / 72 * self.S + 0.5),
                weight="bold" if bold else "normal")
        return self._tkfonts[key]

    def rand(self):
        return self.rng.random()

    def _key(self, e):
        if e.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            self._keys += 1

    @property
    def Width(self):
        return self._width

    @Width.setter
    def Width(self, v):
        # form width; the form grows to the right here (in VFP its left edge moved to the left)
        v = int(round(min(max(v, 100), self.pnW)))
        if v != self._width:
            self._width = v
            self.g.dirty = True
            if self.on_width:
                self.on_width(v)

    def refresh(self):
        img = self.g.img.crop((0, 0, self._width, self.pnH))
        if self.S != 1:
            img = img.resize((int(img.width * self.S), int(img.height * self.S)), Image.BILINEAR)
        if self.tkimg is None or self.tkimg.width() != img.width or self.tkimg.height() != img.height:
            self.tkimg = ImageTk.PhotoImage(img)
            self.bg_label.config(image=self.tkimg)
            self.bg_label.place(x=0, y=0, width=img.width, height=img.height)
        else:
            self.tkimg.paste(img)
        self.g.dirty = False

    def _autorefresh(self):
        # Also refreshes the image when no further DOEVENTS follows.
        if self.dead or self.closed:
            return
        try:
            self.flush()
            self._after_id = self.root.after(40, self._autorefresh)
        except tk.TclError:
            pass

    def stop(self):
        """Stop the form (it is replaced, or the window closes)."""
        self.dead = True
        try:
            if getattr(self, "_after_id", None):
                self.root.after_cancel(self._after_id)
        except tk.TclError:
            pass

    def flush(self):
        while self._dirty_labels:
            self._dirty_labels.pop()._flush()
        if self.g.dirty:
            self.refresh()

    def check(self):
        if self.dead or self.closed:
            raise Stopped()

    def _update(self):
        self.flush()
        self.root.update()
        self._last_ev = time.perf_counter()
        self.check()

    def DOEVENTS(self):
        """DOEVENTS once per program step, paced to the speed of the VFP program: measured in
        VFP 9, a step takes about 0.2 ms + 0.28 ms per NON (20 NONs: 170 steps/s)."""
        self.check()
        now = time.perf_counter()
        self._due += (0.2 + 0.28 * self.SGM.NONQTY) / 1000 / self.speed
        if self._due < now - 0.04:
            self._due = now - 0.04          # no catching up after a slow moment
        if self._due > now + 0.004:
            self._update()
            while True:
                rest = self._due - time.perf_counter()
                if rest <= 0:
                    break
                time.sleep(min(rest, 0.015))
                if rest > 0.015:
                    self._update()
        elif now - self._last_ev > 0.03:
            self._update()

    def WAIT(self, secs):
        """WAIT '' TIMEOUT secs (a key press ends it earlier)."""
        self._keys = 0
        end = time.perf_counter() + secs / self.speed
        while time.perf_counter() < end and self._keys == 0:
            self._update()
            time.sleep(0.015)
        self._keys = 0
        self._due = time.perf_counter()

    def BEEP(self):
        try:
            self.root.bell()             # ?? CHR(7)
        except tk.TclError:
            pass

    def SetAll(self, prop, value, cls=None):
        for c in self.controls.values():
            if cls is None or c.cls == cls:
                setattr(c, prop, value)

    def add(self, ctl):
        self.controls[ctl.Name] = ctl
        setattr(self, ctl.Name, ctl)
        return ctl

    def commit_spinners(self):
        f = self.root.focus_get()
        for c in self.controls.values():
            if isinstance(c, VSpinner) and f is c.entry:
                c._parse()

    def guarded(self, fn, *a):
        """Runs an event procedure; a replaced form (Stopped) simply ends it."""
        self.busy += 1
        try:
            fn(*a)
        except Stopped:
            pass
        finally:
            self.busy -= 1

    # -- building the form (AddObject in Activate) --------------------------
    def build(self):
        pnW, pnH = self.pnW, self.pnH
        # SG_CBU1..6 : switches at the top
        for nX in range(1, 7):
            w = (pnW / 2) / 6
            l = self.add(VLabel(self, "SG_CBU%d" % nX, "SG_CBU",
                                STREXTRACT(",CS1 OFF,CS2 OFF,---,TRACE ON,BEAM ON,METAB.BRAKE ON,", ",", nX),
                                8, pnWit if nX < 3 else pnZwart, pnCyaan))
            l.Tag = l.Caption
            l.place((nX - 1) * w, 0, w, 20)
            if nX == 3:
                l.Enabled = False
                l.Tag = "INTERMIXED"
                l.ToolTipText = ("When 'INTERMIXED' CS1 and CS2 are activated alternately (but still randomly)," + pcCR +
                                 "when 'COMPOUNDED' CS2 always follows CS1 and only then is the US supposed to happen :" + pcCR +
                                 "Programmatically it is implemented by disabling LTD (since both CSs are active when the US occurs)" + pcCR +
                                 "and by using the combined sums of SSs in the calculations.")
            elif nX == 6:
                l.ToolTipText = ("Activating the 'metabolic brake' is a 'shift of view' :" + pcCR +
                                 "LTP saturation is no more viewed as a local synapse related phenomenon" + pcCR +
                                 "but as a whole cell phenomenon : the metabolic resources put a limit on the amount of LTP the cell can maintain." + pcCR +
                                 "Programmatically it is implemented by having a decline in terminal connection chance at the NON level"
                                 " when LTP in the NON goes up.")
            l.w.bind("<Button-1>", lambda e, l=l: l.Enabled and self.guarded(self.CBU_Click, l))

        # SG_CBD1..3 : RUN / STOP / ABORT
        for nX in range(1, 4):
            w = (pnW / 2) / 3
            l = self.add(VLabel(self, "SG_CBD%d" % nX, "SG_CBD", STREXTRACT(",RUN,STOP,ABORT,", ",", nX), 8))
            l.place((nX - 1) * w, 20, w, 20)
            if nX == 2:
                l.Enabled = False
                l.ToolTipText = ("Interrupts the run, click 'CONTINUE' to resume where it was halted." + pcCR +
                                 "You can use the 'run steps' setting to interrupt automatically after x steps.")
            elif nX == 3:
                l.ToolTipText = "Aborts the run, click 'RUN' to restart."
            l.w.bind("<ButtonPress-1>", lambda e, l=l: l.Enabled and self.guarded(self.CBD_MouseDown, l))

        # SG_SPLB1..11 (captions above the spinners) + SG_SP1..11 (spinners)
        caps = (",NON quantity,LTP gain,LTD gain,CR (US brake) from,LTP brake from,Random factor,Background noise,"
                "Term. conn. chance one over x,STOP limit,Demo,Run x steps and interrupt,")
        tips = [None,
                "Sets the number of displayed 'nanoloops' (NONs, PuCs ...) to x.",
                "A lower x value prolongs the run, showing a more detailed time course.",
                "Without LTD (x=0) there is no segregation. A high LTD gain speeds up segregation, "
                "but then 'double peaks' barely get a chance to appear.",
                "At this value of SUMSS (the active part) the US starts to be subdued by an upcoming CR." + pcCR +
                "When x is set low a long period of double peaks appears, if set high they may not appear at all.",
                "At x % of max LTP (10), LTP increase starts to slow down." + pcCR +
                "In 'single view' (at the synapse) it takes in account only the ACTIVE synapse." + pcCR +
                "In 'population view' it is interpreted that metabolic resources start to fall short to sustain the "
                "required LTP level cell wide," + pcCR +
                "and hence (when 'metab. brake is ON') the calculation is based on the sum of all SSs (active and nonactive).",
                "The random factor for LTP co-determines the speed of segregation : when x=0 no segregation occurs.",
                "Sets the % of background noise (here simulated by low frequency activation of the inactive competing CS).",
                "Sets the chance for terminals to connect to NONs at the beginning of the run," + pcCR +
                "before the metabolic brake and declining US strength step in to lower it." + pcCR +
                "Read the chance as 1/x at each step for each terminal." + pcCR +
                "Keeping the chances high (x=1) raises the probability for double connections"
                " - needed to have an initial 'double peak phenomenon'.",
                "Ends the run when x% of maximum SumSS (the CR is a function of it) is reached." + pcCR +
                "Set at 100% to keep a run going on indefinitely.",
                "Sets the demo values for demo x . Move the cursor over the up- or downclick button to see a "
                "description of the demo.",
                "Interrupts the run every x steps, click on CONTINUE to resume."]
        #       NONQTY  LTP   LTD   CR_TH  LTP_BR_TH  RAND  BGN  INICHANCE  STOPLIM  Demo nr  RunSteps
        LOW = [0, 6,    0.1,  0.0,  0,     0,         0.0,  0,   0,         10,      0,       0]
        HIGH = [0, 100, 5,    5,    99,    100,       10.0, 100, 5000,      100,     14,      500]
        INC = [0, 2,    0.1,  0.1,  1,     1,         0.1,  1,   10,        1,       1,       10]
        for nX in range(1, 12):
            w = (pnW / 2) / 11
            b = self.add(VButton(self, "SG_SPLB%d" % nX, "SG_SPLB", STREXTRACT(caps, ",", nX), 6))
            b.ToolTipText = tips[nX]
            b.place((nX - 1) * w, pnH - 60, w, 30)
            # Init value; for SG_SP1..9 the bound field (ControlSource = FIELD(nX)) supplies the value
            value = getattr(self.SGM, FIELDS[nX - 1]) if nX <= 9 else 0
            sp = self.add(VSpinner(self, "SG_SP%d" % nX, LOW[nX], HIGH[nX], INC[nX], value))
            sp.place((nX - 1) * w, pnH - 30, w, 30)
            if nX <= 9:      # Valid: REPLACE field WITH this.Value
                sp.on_user = lambda d, sp=sp, f=FIELDS[nX - 1]: setattr(self.SGM, f, sp.Value)
            elif nX == 10:   # UpClick / DownClick
                sp.on_user = lambda d: d != 0 and self.guarded(self.SP10_UpClick)

    def activate(self):
        # Activate: only once (lSEGREG)
        if self.dead or self.closed or getattr(self, "lSEGREG", False):
            return
        self.lSEGREG = True
        self.busy += 1
        try:
            if self.plCalled:
                self.DEMO()
            else:
                self.DORUN(False)
        except Stopped:
            pass
        finally:
            self.busy -= 1

    # -- PROCEDURE DEMO ------------------------------------------------------
    def DEMO(self, lNoRun=False):
        try:
            nCMD = int(self.pcCMD)
        except ValueError:
            nCMD = 0
        self.plRun = True
        S = self.SGM
        S.replace(**DEMO_SGM)
        self.LOADSPS()
        if self.plCalled and not self.plIA:     # which controls a demo shows (article version of the program)
            self.SetAll("Visible", False)
            if nCMD > 4:
                self.SetAll("Visible", True, "SG_SPLB")
                self.SetAll("Visible", True, "SG_SP")
                self.SetAll("Enabled", False, "SG_SP")
                self.SG_CBU3.Visible = True
                self.SG_CBU3.Enabled = False
                self.SG_CBU4.Visible = True
                self.SG_CBU5.Visible = True
                self.SG_CBU6.Visible = True
                self.SG_CBU6.Enabled = False
            if nCMD > 7:
                self.SG_CBU6.Enabled = True
            self.SG_CBU1.Visible = True
            self.SG_CBU2.Visible = True
            self.SG_CBD3.Visible = True
        # First DORUN always with .F. to initialize values
        if nCMD == 1:      # Presentation of demo components
            self.SETTINGS("ON", "ON", "I", "ON", "ON", "OFF")
            self.DORUN(False, 100, lNoRun)
        elif nCMD == 2:    # Showing thickening lines
            self.SETTINGS("ON", "ON", "I", "ON", "ON", "OFF")
            self.DORUN(False, 345, lNoRun)
        elif nCMD == 3:    # Showing Gauss curves
            self.SETTINGS("ON", "ON", "I", "ON", "ON", "OFF")
            self.DORUN(False, 500, lNoRun)
        elif nCMD == 4:    # Complete run, intermixed, trace off, showing the segregation process
            self.SETTINGS("ON", "ON", "I", "OFF", "ON", "OFF")
            self.DORUN(False, 6700, lNoRun)
        elif nCMD == 5:    # Trace divergence demo with 10 NONs, random function enabled
            self.SETTINGS("ON", "ON", "I", "ON", "OFF", "OFF")
            S.replace(NONQTY=10)
            self.DORUN(False, 8000, lNoRun)
        elif nCMD == 6:    # Trace divergence demo with 10 NONs, random function disabled
            self.SETTINGS("ON", "ON", "I", "ON", "OFF", "OFF")
            S.replace(NONQTY=10, RAND=0)
            self.DORUN(False, 4500, lNoRun)
        elif nCMD == 7:    # 'Transfer training' CS1->CS2->CS1 with M-BRAKE OFF
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "OFF")
            if lNoRun:
                return
            S.replace(CR_TH=5)
            self.DORUN(False, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("OFF", "ON", "I", "ON", "ON", "OFF")
            self.DORUN(True, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "OFF")
            self.DORUN(True, 6700, lNoRun)
        elif nCMD == 8:    # 'Transfer training' CS1->CS2->CS1 with M-BRAKE ON
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "ON")
            if lNoRun:
                return
            S.replace(CR_TH=5)
            self.DORUN(False, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("OFF", "ON", "I", "ON", "ON", "ON")
            self.DORUN(True, 5000, lNoRun)
        elif nCMD == 9:    # CS1 CS2 INTERMIXED with M-BRAKE ON
            self.SETTINGS("ON", "ON", "I", "ON", "ON", "ON")
            S.replace(CR_TH=5)
            self.DORUN(False, 6700, lNoRun)
        elif nCMD == 10:   # 'Transfer training' CS1->CS2 with M-BRAKE ON, running longer to watch 'erosion' of CS1
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "ON")
            if lNoRun:
                return
            S.replace(CR_TH=5)
            self.DORUN(False, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("OFF", "ON", "I", "ON", "ON", "ON")
            S.replace(STOPLIM=100)
            self.DORUN(True, 4000, lNoRun)
            self.WAIT(2)
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "ON")
            S.replace(STOPLIM=90)
            self.DORUN(True, 5000, lNoRun)
        elif nCMD == 11:   # 'Transfer training' CS1->CS2->CS1 with M-BRAKE ON AND Background noise
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "ON")
            S.replace(CR_TH=5)
            S.replace(BGN=5)
            if lNoRun:
                return
            self.DORUN(False, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("OFF", "ON", "I", "ON", "ON", "ON")
            self.DORUN(True, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("ON", "OFF", "I", "ON", "ON", "ON")
            self.DORUN(True, 6700, lNoRun)
        elif nCMD == 12:   # Interactive mode
            self.SetAll("Visible", True)
            self.SetAll("Enabled", True)
            self.SETTINGS("ON", "ON", "I", "ON", "ON", "ON")
            self.DORUN(False, 0, True)
        elif nCMD == 13:   # CS1 CS2 COMPOUNDED with M-BRAKE ON AND Background noise
            self.SetAll("Visible", True)
            self.SETTINGS("ON", "ON", "C", "ON", "ON", "ON")
            S.replace(CR_TH=5)
            S.replace(BGN=5, LTD=0)
            self.DORUN(False, 2000, lNoRun)
        elif nCMD == 14:   # Pretraining with CS2 followed by 'simultaneous' COMPOUND training with CS1 and CS2
            self.SetAll("Visible", True)
            self.SETTINGS("OFF", "ON", "I", "ON", "ON", "ON")
            if lNoRun:
                return
            self.DORUN(False, 6700, lNoRun)
            self.WAIT(2)
            self.SETTINGS("ON", "ON", "C", "ON", "ON", "ON")
            S.replace(CR_TH=30, BGN=5, LTD=0)
            self.DORUN(True, 4000, lNoRun)
        else:
            return
        # (In VFP two DblClicks bring a widened form back to half the screen width.)
        if self.Width > self.pnW / 2:
            self.Width = self.pnW / 2

    # -- PROCEDURE SETTINGS --------------------------------------------------
    def SETTINGS(self, *c):
        for nX in range(1, 7):
            ctl = self.controls["SG_CBU%d" % nX]
            cCap, cX = ctl.Caption, c[nX - 1]
            if cX.startswith("O"):        # SET EXACT OFF: c='O' is true for "ON" and "OFF"
                ctl.Caption = cCap[:cCap.rfind(" ") + 1] + cX
                if nX == 1:
                    self.SG_CBU1.ForeColor = pnRood if cX == "ON" else pnWit
                elif nX == 2:
                    self.SG_CBU2.ForeColor = pnBlauw if cX == "ON" else pnWit
            else:
                ctl.Caption = "INTERMIXED" if c[2] == "I" else "COMPOUNDED"
                ctl.Tag = ctl.Caption

    # -- PROCEDURE LOADSPS ---------------------------------------------------
    def LOADSPS(self):
        if self.SGM.LTP > 0:
            for nX in range(1, 10):
                self.controls["SG_SP%d" % nX].Value = getattr(self.SGM, FIELDS[nX - 1])

    # -- PROCEDURE DORUN -----------------------------------------------------
    def DORUN(self, lCont=False, nSteps=None, lNoRun=False):
        if lNoRun:
            return
        g, S, SS, SUMSS, TERMS = self.g, self.SGM, self.SS, self.SUMSS, self.TERMS
        # INITIALISATION
        self.pnHOffSet = 80              # Horizontal offset
        self.pnVOffSet = 75              # Vertical offset
        self.pnDist = 380 / S.NONQTY     # Distance between NONs
        self.pnHPosNON = 200             # Position of NON column
        self.pnHPosPuC = 315             # Position of PuC column
        self.pnRad = 10                  # radius
        if self.SG_CBD1.Caption == "RUN":
            self.Width = self.pnW / 2
        self.LOADSPS()
        self.SG_CBD2.Enabled = True

        N = int(S.NONQTY)
        for i in (1, 2):                 # DIMENSION SS[2,NONQTY]
            while len(SS[i]) <= N:
                SS[i].append(0.0)
        if not lCont:   # If it is NOT a 'continuing' of an earlier procedure then we initialize the values
            self.pnSteps = self.pnStepsTot = 0
            for nX in (1, 2):
                SUMSS[nX] = 0.0
                self.SUMSSCR1[nX] = 0.0
                self.SUMSSCR2[nX] = 0.0
                TERMS[nX] = [0] * (N + 1)
                for nY in range(1, N + 1):
                    SS[nX][nY] = 0.0
        for i in (1, 2):
            while len(TERMS[i]) <= N:
                TERMS[i].append(0)
        if not self.plRun:
            return

        self.running = True
        try:
            self._dorun(lCont, nSteps, N)
        finally:
            self.running = False

    def _dorun(self, lCont, nSteps, N):
        g, S, SS, SUMSS, TERMS = self.g, self.SGM, self.SS, self.SUMSS, self.TERMS
        # RENDERING SECTION vvvvvvvv
        nK = 0
        nSH = 70
        sh = nSH if N > 15 else 0
        pnHOffSet, pnVOffSet, pnDist = self.pnHOffSet, self.pnVOffSet, self.pnDist
        pnHPosNON, pnHPosPuC, pnRad = self.pnHPosNON, self.pnHPosPuC, self.pnRad
        g.ForeColor = pnZwart
        nVO = pnVOffSet + pnDist * (N - 1) + 10
        g.Print("MFs", (pnHOffSet + pnHPosNON) / 2, nVO + 5)
        g.Print("NONs", pnHPosNON - pnRad, nVO + 5)
        g.Print("CFs", (pnHPosNON + pnHPosPuC + sh) / 2 - pnRad / 2, nVO + 5)
        g.Print("PuCs", pnHPosPuC + sh - pnRad, nVO + 5)
        nVO = nVO + 60
        g.ForeColor = pnRood
        g.Line(0, pnVOffSet, pnHOffSet, pnVOffSet)   # Hor MF line
        g.Print("800 ms", 60, nVO / 2 - 20)
        g.ForeColor = pnBlauw
        g.Line(0, pnVOffSet + pnDist * (N - 1), pnHOffSet, pnVOffSet + pnDist * (N - 1))   # Hor MF line
        g.Print("400 ms", 14, nVO / 2 + 115)
        # RENDERING SECTION ^^^^^^^^

        lCS1 = self.SG_CBU1.Caption == "CS1 ON"
        lCS1Mem = lCS1
        lCS2 = self.SG_CBU2.Caption == "CS2 ON"
        lCS2Mem = lCS2
        lCPD = self.SG_CBU3.Caption == "COMPOUNDED"
        if lCPD:
            lCS1 = False
        self.SG_CBU1.ForeColor = pnRood if lCS1 else pnWit
        self.SG_CBU2.ForeColor = pnBlauw if lCS2 else pnWit

        self.pnSatELTP = 10                                    # the LTP saturation limit of the NON (for all CS input together in 'population view')
        self.pnSatBLTP = self.pnSatELTP * S.LTP_BR_TH / 100   # The set threshold above which the LTP brake starts to have effect
        nSUMSS_TH = self.pnSatELTP * N * S.CR_TH / 100
        nMax = nSteps if isinstance(nSteps, (int, float)) else 100000
        self._due = self._last_ev = time.perf_counter()

        while self.pnSteps < nMax:
            if not lCS1 and not lCS2:            # No CS selected
                break
            if lCPD:          # Switches CS1=.F./CS2=.T. with CS1=.T./CS2=.F. (therefore CS1 must be =.F. at the start)
                lCS1, lCS2 = lCS2, lCS1
                self.SG_CBU1.ForeColor = pnRood
            elif lCS1Mem and lCS2Mem:   # when 'Intermixed' CS1 and CS2 are chosen at random in equal frequency
                lCS1 = self.rand() < .5
            elif lCS1Mem:     # Background noise ! lCS1=.T. but in SGM.BGN/100 of cases it is .F. and then lCS2 will be .T.
                lCS1 = self.rand() < 1 - S.BGN / 100
            elif lCS2Mem:     # Background noise ! lCS2=.T. but in SGM.BGN/100 of cases it is .F. and then lCS1 will be .T.
                lCS1 = self.rand() < S.BGN / 100
            lCS2 = not lCS1
            nCS = 1 if lCS1 else 2

            for i in range(len(TERMS[1])):
                TERMS[1][i] = 0
                TERMS[2][i] = 0
            self.CSALL(nCS, lCPD)

            # RENDERING SECTION vvvvvvvv
            nF = (20 / 100) * 20 / N   # to keep the maximum curve top equally high when different numbers of NONs are displayed
            nVO = pnVOffSet + pnDist * (N - 1) / 2
            if self.pnSteps % 10 == 0:
                nDW = 1
                C1, C2 = self.SUMSSCR1, self.SUMSSCR2
                g.ForeColor = g.BackColor   # Erasing the curves
                self.GAUSS(nVO - 20, 46, C1[1] * nF, nDW)    # CR by CS1 via timers of CS1 ('tone' with US at 800 ms)
                self.GAUSS(nVO - 20, 0, C2[1] * nF, nDW)     # CR by CS2 via timers of CS1 ('tone' with US at 800 ms)
                self.GAUSS(nVO + 115, 0, C2[2] * nF, nDW)    # CR by CS2 via timers of CS2 ('light' with US at 400 ms)
                self.GAUSS(nVO + 115, 46, C1[2] * nF, nDW)   # CR by CS1 via timers of CS2 ('light' with US at 400 ms)
                # -20 = curves when testing CS1, +115 = curves when testing CS2; '0' = 400 ms, '46' = 800 ms
                self.SUM_SSCR(nCS, lCPD)   # Get the new SUMSS values
                g.ForeColor = pnRood       # Drawing the curves of CS1 on the basis of the sum of SSs
                if lCPD:
                    # If two CSs "cooperate" in 'compound' we must also check if the individual CS has enough power
                    # to activate CFs since once it does it activates timers of CS1 as well as CS2
                    # and if e.g. CS1 is still very weak it should not activate timers made by CS2
                    if SUMSS[1] + SUMSS[2] > nSUMSS_TH:
                        self.GAUSS(nVO - 20, 46, C1[1] * nF, nDW)
                        if SUMSS[2] > nSUMSS_TH:
                            self.GAUSS(nVO + 115, 46, C1[2] * nF, nDW)
                    g.ForeColor = pnBlauw  # Drawing the curves of CS2
                    if SUMSS[2] + SUMSS[1] > nSUMSS_TH:
                        self.GAUSS(nVO + 115, 0, C2[2] * nF, nDW)
                        if SUMSS[1] > nSUMSS_TH:
                            self.GAUSS(nVO - 20, 0, C2[1] * nF, nDW)
                else:
                    self.GAUSS(nVO - 20, 46, C1[1] * nF, nDW)
                    self.GAUSS(nVO + 115, 46, C1[2] * nF, nDW)
                    g.ForeColor = pnBlauw  # Drawing the curves of CS2
                    self.GAUSS(nVO + 115, 0, C2[2] * nF, nDW)
                    self.GAUSS(nVO - 20, 0, C2[1] * nF, nDW)

            self.pnStepFactor = 30   # determines progression speed of trace and 'beam' on the screen
            if self.pnSteps % self.pnStepFactor == 0:
                if pnHPosPuC + sh + 10 + self.pnSteps / self.pnStepFactor > self.Width - 5:
                    self.Width = self.Width + 1   # the screen widens
            if pnHPosPuC + sh + 10 + self.pnSteps / self.pnStepFactor > self.pnW:   # when full screen is attained, restart display
                g.Cls()
                self.pnSteps = 0
            self.pnSteps += 1
            self.pnStepsTot += 1

            g.ForeColor = pnRood
            g.Print("Sum CS1=" + STR(SUMSS[1], 7, 2), 5, pnVOffSet - 15)   # SUM of all CS1 SSs
            g.Print("CS1 : %d terminals  " % self.nTerms(TERMS[1]), 5, pnVOffSet - 25)   # Count of connected CS1 terminals
            g.ForeColor = pnBlauw
            g.Print("Sum CS2=" + STR(SUMSS[2], 7, 2), 5, pnVOffSet + pnDist * (N - 1) + 6)
            g.Print("CS2 : %d terminals  " % self.nTerms(TERMS[2]), 5, pnVOffSet + pnDist * (N - 1) + 16)
            g.ForeColor = pnZwart
            g.Print("%d steps " % self.pnStepsTot, 5, pnVOffSet + pnDist * (N - 1) / 2 - 6)   # StepCount
            # RENDERING SECTION ^^^^^^^^

            self.DOEVENTS()

            # Ending the procedure
            lim = self.pnSUMSS_EUS * S.STOPLIM / 100
            n100_1 = sum(1 for i in range(1, N + 1) if TERMS[1][i] == 100)
            n100_2 = sum(1 for i in range(1, N + 1) if TERMS[2][i] == 100)
            if not lCS1Mem or (n100_1 >= N / 2 and SUMSS[1] > lim):
                if not lCS2Mem or (n100_2 >= N / 2 and SUMSS[2] > lim):
                    if nK == 300:   # keep running for 300 steps after ending requirements are fulfilled
                        break
                    nK += 1

            # Stopping / Interrupting the procedure
            v11 = self.SG_SP11.Value
            if v11 > 0 and self.pnSteps % v11 == 0:   # Interrupt after each x steps when desired
                self.CBD_MouseDown(self.SG_CBD2)        # Stop button
            if self.plStop:
                self.plStop = False
                self.SG_CBD1.Caption = "CONTINUE"
                break
            # Aborting the procedure
            if self.plAbort:
                self.SG_CBD1.Caption = "RUN"
                break

        for nX in range(1, N + 1):
            nVO = pnVOffSet + pnDist * (nX - 1)
            g.ForeColor = pnRood
            self.LINEDRAW(1, SS[1][nX] + 1, True, nVO)   # Erasing
            if SS[1][nX] > .1:
                self.LINEDRAW(1, SS[1][nX], False, nVO)  # Redrawing
            g.ForeColor = pnBlauw
            self.LINEDRAW(2, SS[2][nX] + 1, True, nVO)
            if SS[2][nX] > .1:
                self.LINEDRAW(2, SS[2][nX], False, nVO)
            # Redrawing of NONs to erase overlying line endings
            g.DrawWidth = 1
            g.FillColor = pnCyaan
            g.Circle(pnRad, pnHPosNON, nVO)
        self.SetAll("Enabled", True, "SG_SP")
        self.BEEP()
        self.flush()

    @staticmethod
    def nTerms(T):
        """LEN(TERMS)-OCCURS(CHR(0),TERMS)-OCCURS(CHR(1),TERMS): terminals with more than 1 % of the NON's SS"""
        return sum(1 for v in T[1:] if v > 1)

    # -- PROCEDURE CSALL -----------------------------------------------------
    def CSALL(self, nCS, lCPD):
        self.SUM_SS()
        self.LTPD(nCS, lCPD)
        self.DEL_TERM()
        self.ADD_TERM(nCS, lCPD)

    # US present from beginning, LTPing active synapses, LTDing inactive synapses, geometrically.
    # PuC timed CRs can only start to develop when individual NONs become able to HP-R IO cells (hence from an LTP threshold on)
    # US only starts to dwindle when overt CRs appear, i.e. above a threshold of summed SS of the CS
    #    to disappear gradually above a limit of summed SS
    # Terminals are supposed to increase with US strength (and stop to do so when US dwindles)
    #    hence at a constant rate when US stays constant, but it should be much slower than LTP increase.
    # Terminals 'disengage' when LTP goes under a limit
    # Terminals also 'disengage' when US strength goes under a limit

    # -- PROCEDURE LTPD ------------------------------------------------------
    def LTPD(self, nCSP, lCPD):
        g, S, SS, SUMSS, TERMS = self.g, self.SGM, self.SS, self.SUMSS, self.TERMS
        N = int(S.NONQTY)
        pnVOffSet, pnDist, pnHPosNON, pnHPosPuC, pnRad = self.pnVOffSet, self.pnDist, self.pnHPosNON, self.pnHPosPuC, self.pnRad
        pnSatELTP, pnSatBLTP = self.pnSatELTP, self.pnSatBLTP
        nCSD = 2 if nCSP == 1 else 1       # nCSP refers to the active synapse, nCSD to the inactive one
        # Rendering settings
        nSH = 70
        xPuC = pnHPosPuC + (nSH if N > 15 else 0)
        g.FillStyle = 0                    # Solid
        nCSColor = pnRood if nCSP == 1 else pnBlauw
        g.ForeColor = nCSColor
        brake = self.SG_CBU6.Caption == "METAB.BRAKE ON"
        rnd = self.rand
        p = self.pnSteps

        # Calculations per NON
        for nX in range(1, N + 1):
            nMemSSP, nMemSSD = SS[nCSP][nX], SS[nCSD][nX]
            # Calculation of LTP on the active synapse
            nSS12 = SS[1][nX] + SS[2][nX]   # the sum of the two synapses on the NON
            self.pnSUMSS_EUS = pnSatELTP * N / 2   # at this value of SUMSS the US is neutralized by negative feedback from the CR
            self.pnSUMSS_BUS = S.CR_TH             # at this value of SUMSS (of active synapses) the US starts to be subdued by an upcoming CR
            # When SGM.CR_TH is set low a long period of double peaks appears, if set high they may not appear at all
            EUS, BUS = self.pnSUMSS_EUS, self.pnSUMSS_BUS
            if lCPD:   # In case of 'compound' CS1 and CS2 training
                nUS_Brake = div(SUMSS[1] + SUMSS[2] - BUS, EUS - BUS)
                nUS_Brake = EUS * (1 if SUMSS[1] + SUMSS[2] < BUS else 1 - nUS_Brake)
                # Range 0 to 1, is inverse parameter of US strength; depends on the strength of ALL ACTIVE synapses;
                # effect starts to show when SUMSS=>pnSUMSS_BUS
                nLTP_Brake = div(nSS12 - pnSatBLTP, pnSatELTP - pnSatBLTP)
                nLTP_Brake = pnSatELTP * (1 if nSS12 < pnSatBLTP else 1 - nLTP_Brake)
                SS[1][nX] = SS[1][nX] * (1 + SS[1][nX] * S.LTP * nLTP_Brake * nUS_Brake * (rnd() * S.RAND / 10 + .5) / 10000)
                SS[2][nX] = SS[2][nX] * (1 + SS[2][nX] * S.LTP * nLTP_Brake * nUS_Brake * (rnd() * S.RAND / 10 + .5) / 10000)
            else:      # In case of 'intermixed' CS1 and CS2 training
                nUS_Brake = div(SUMSS[nCSP] - BUS, EUS - BUS)
                nUS_Brake = EUS * (1 if SUMSS[nCSP] < BUS else 1 - nUS_Brake)
                nSS = nSS12 if brake else SS[nCSP][nX]
                nLTP_Brake = div(nSS - pnSatBLTP, pnSatELTP - pnSatBLTP)
                nLTP_Brake = pnSatELTP * (1 if nSS < pnSatBLTP else 1 - nLTP_Brake)
                SS[nCSP][nX] = SS[nCSP][nX] * (1 + SS[nCSP][nX] * S.LTP * nLTP_Brake * nUS_Brake * (rnd() * S.RAND / 10 + .5) / 10000)
            SS[nCSP][nX] = max(0.0, SS[nCSP][nX])   # protect against negative undershoots
            # LTP is a function of actual ACTIVE SS, LTP gain, distance to LTP saturation, US strength (dwindles above CR-TH), and a random factor

            # Calculation of LTD on the inactive synapse (when 'compounded' there is NO LTD !!)
            if not lCPD:
                SS[nCSD][nX] = SS[nCSD][nX] * (1 - min(1, SS[nCSP][nX] * S.LTD * (rnd() * S.RAND / 10 + .5) / 100))
                # LTD is a function of actual INACTIVE CS, LTD gain,
                # but also of actual ACTIVE SS (and hence also of all factors determining LTP), and a random factor
                SS[nCSD][nX] = max(0.0, SS[nCSD][nX])
            nSS12 = SS[1][nX] + SS[2][nX]

            # To keep track in how far each 'terminal' is saturated (i.e. when = 100, and all active terminals saturated, the process can stop)
            if nSS12 > 0:
                TERMS[nCSP][nX] = INT(SS[nCSP][nX] * 100 / nSS12)
                TERMS[nCSD][nX] = INT(SS[nCSD][nX] * 100 / nSS12)

            # RENDERING SECTION vvvvvvvv
            # erasing of active MF-NON lines and redrawing them when the width changed
            nVO = pnVOffSet + pnDist * (nX - 1)
            if INT(nMemSSP) != INT(SS[nCSP][nX]) or nMemSSP < 1 or p < 100 or p % 100 == 0:
                if nMemSSP > 0.05:   # with 0 erased stripes remain, with 1 colour lines of 1 remain, .05 solves it
                    self.LINEDRAW(nCSP, nMemSSP + 2, True, nVO)   # Erasing
                self.LINEDRAW(nCSP, SS[nCSP][nX], False, nVO)     # Redrawing
            # erasing of inactive MF-NON lines and redrawing them when the width changed
            if INT(nMemSSD) != INT(SS[nCSD][nX]) or nMemSSD < 1 or p < 100 or p % 100 == 0:
                if nMemSSD > 0.05:
                    self.LINEDRAW(nCSD, nMemSSD + 2, True, nVO)   # Erasing
                self.LINEDRAW(nCSD, SS[nCSD][nX], False, nVO)     # Redrawing

            # Relative and absolute values of CS1-SS and CS2-SS
            if N <= 26:
                t1 = STR(div(SS[1][nX] * 100, nSS12), 4) + " CS1=" + STR(SS[1][nX], 7, 3) + " "
                t2 = STR(div(SS[2][nX] * 100, nSS12), 4) + " CS2=" + STR(SS[2][nX], 7, 3) + " "
                if N > 15:
                    g.ForeColor = pnRood
                    g.Print(t1, pnHPosNON + 7, nVO - 8 - 4)          # Figures above the horizontal NON-PuC line
                    g.ForeColor = pnBlauw
                    g.Print(t2, pnHPosNON + 17 + nSH, nVO - 8 - 4)   # Figures above the horizontal NON-PuC line
                else:
                    g.ForeColor = pnRood
                    g.Print(t1, pnHPosNON + 12, nVO - 8 - 5)         # Figures above the horizontal NON-PuC line
                    g.ForeColor = pnBlauw
                    g.Print(t2, pnHPosNON + 12, nVO + 8 - 4)         # Figures under the horizontal NON-PuC line
            # Erasing the horizontal line between NON and PuC
            g.ForeColor = g.BackColor
            g.DrawWidth = 5
            g.Line(pnHPosNON, nVO, xPuC, nVO)
            # Redrawing the horizontal line between NON and PuC
            nMixColor = RGB(div(255 * SS[1][nX], nSS12), 0, div(255 * SS[2][nX], nSS12))   # Mixed colour of the horizontal line
            mix = rgb_tuple(nMixColor)
            if nMixColor > 0:
                g.ForeColor = mix
                g.DrawWidth = 5 if nSS12 > abs(S.CR_TH) / 10 else 1   # Line width of the horizontal line
                # The maximum of nSS12 is 20 (2 synapses of max 10 when saturated); SGM.CR_TH/10 goes from 0 to 10.
                # CR-TH is used here as the threshold above which CF firing starts, while elsewhere it is used as
                # the threshold above which the CR starts to appear.  The thickening of the line is 'cosmetic' and
                # the CF threshold is of no further consequence in the calculation because a higher CR threshold
                # follows.  It would complicate needlessly the calculation to implement a 'two-stage threshold'.
                g.Line(pnHPosNON, nVO, xPuC, nVO)
                g.DrawWidth = 1
                g.FillColor = mix
                g.Circle(pnRad, xPuC, nVO)   # draws a full circle PuC of the same colour as the NON-PuC line
            # Beam progress
            if self.SG_CBU5.Caption == "BEAM ON":
                g.ForeColor = mix
                g.DrawWidth = 1
                if nSS12 > abs(S.CR_TH) / 10 and nMixColor > 0:
                    x = xPuC + 10 + div(p, self.pnStepFactor)   # with more than 15 NONs the distance NON-PuC widens by nSH
                    g.Line(x, nVO - pnDist / 2, x, nVO + pnDist / 2 + 1)
            # Trace progress
            if self.SG_CBU4.Caption == "TRACE ON" and SS[nCSP][nX] > 0:
                g.ForeColor = nCSColor
                g.DrawWidth = 1
                g.PSet(xPuC + 9 + div(p, self.pnStepFactor), nVO + 1 - (20 / N) * SS[nCSP][nX])
            # Redrawing of NONs to erase overlying line endings
            g.FillColor = pnCyaan
            g.Circle(pnRad, pnHPosNON, nVO)
            # RENDERING SECTION ^^^^^^^^

    # -- PROCEDURE SUM_SS ----------------------------------------------------
    def SUM_SS(self):
        SS, N = self.SS, int(self.SGM.NONQTY)
        self.SUMSS[1] = sum(SS[1][1:N + 1])
        self.SUMSS[2] = sum(SS[2][1:N + 1])

    # -- PROCEDURE SUM_SSCR: has to represent the CRs when testing is done for CS1 or CS2 ALONE !!!
    def SUM_SSCR(self, nCS, lCPD):
        SS, N, C1, C2 = self.SS, int(self.SGM.NONQTY), self.SUMSSCR1, self.SUMSSCR2
        C1[1] = C1[2] = C2[1] = C2[2] = 0.0
        # Calculation of CR strength.  It is assumed that the (eventually combined) SS of the NON determines the
        # strength of CF firing, and that this in turn determines the strength of HP in the PuC (by the number of
        # activated timers) (the two-stage threshold), and hence 'activating CF' means 'activating the CR'.
        nSS_TH = self.pnSatELTP * self.SGM.CR_TH / 100
        if lCPD:
            # The upper peaks show the CR components of CS1 and CS2 that will fuse when tested for T (displaying an acceleration effect)
            # The lower peaks show the CR components of CS1 and CS2 that will fuse when tested for L (displaying a deceleration effect)
            # However, the demo setup only shows the nanoloop population that has to be 'segregated'.
            # In vivo, there will be other nanoloop populations which from the start on are CS1 only or CS2 only
            # and these components have to be added to complete the final picture
            for nX in range(1, N + 1):
                nSS12 = SS[1][nX] + SS[2][nX]
                if nSS12 > nSS_TH:   # CS1 + CS2 strong enough to trigger the CF-PuC-CR chain
                    C1[1] += SS[1][nX]   # SS gives a measure of how many timers were produced by CS1
                    C2[1] += SS[2][nX]   # SS gives a measure of how many timers were produced by CS2
                    C1[2] += SS[1][nX]
                    C2[2] += SS[2][nX]
        else:
            for nX in range(1, N + 1):
                if SS[1][nX] > nSS_TH:   # CS1 strong enough to trigger the CF-PuC-CR chain
                    # Only the SSs of nanoloops that can trigger a CF are included for the summing
                    C1[1] += SS[1][nX]   # timers produced by CS1 (CS1 U 800)
                    C2[1] += SS[2][nX]   # timers produced by CS2 (CS2 U 400)
                if SS[2][nX] > nSS_TH:   # CS2 strong enough to trigger the CF-PuC-CR chain
                    C2[2] += SS[2][nX]   # timers produced by CS2 (CS2 D 400)
                    C1[2] += SS[1][nX]   # timers produced by CS1 (CS1 D 800)
        # The result gives strengths for four 'CR curves': two for activation by CS1 and two for activation by CS2.
        # If CS1 and CS2 differ in ISI relative to the US, the components are executed after the specific ISI (400 or 800 ms).

    # -- PROCEDURE DEL_TERM --------------------------------------------------
    def DEL_TERM(self):
        SS, N = self.SS, int(self.SGM.NONQTY)
        for nX in range(1, N + 1):
            nVO = self.pnVOffSet + self.pnDist * (nX - 1)
            # When the terminal strength drops below .1 it is 'released': at 0 it is no longer sensitive to LTP
            if 0 < SS[1][nX] < .1:
                SS[1][nX] = 0.0
                self.LINEDRAW(1, 1, True, nVO)   # erase MF-NON line
            if 0 < SS[2][nX] < .1:
                SS[2][nX] = 0.0
                self.LINEDRAW(2, 1, True, nVO)   # erase MF-NON line

    # -- PROCEDURE ADD_TERM --------------------------------------------------
    def ADD_TERM(self, nCS, lCPD):
        S, SS, SUMSS, N = self.SGM, self.SS, self.SUMSS, int(self.SGM.NONQTY)
        nCSD = 2 if nCS == 1 else 1
        brake = self.SG_CBU6.Caption == "METAB.BRAKE ON"
        nUS_Brake = nSS12 = 0
        for nX in range(1, N + 1):
            if lCPD:
                if brake:
                    nSS12 = (SS[1][nX] + SS[2][nX]) / 10
                    # SS range 0 to 10, is parameter for LTP strength: the more SS approaches LTPMAX (lim=10) the smaller
                    # the chance to make a connection; both active and inactive SS values are combined now
                if SS[1][nX] == 0 and SUMSS[1] < self.pnSUMSS_EUS:   # no connection, and not yet saturation of all lines
                    nUS_Brake = 0   # Range 0 to 1, is inverse parameter of US strength
                    nTR = S.INICHANCE + 5000 * nUS_Brake + 5000 * nSS12
                    if 0 <= self.rand() * nTR * S.RAND / 10 <= 1:
                        SS[1][nX] = .1   # When set = 0.1 'sensitivity' for LTP returns
                if SS[2][nX] == 0 and SUMSS[2] < self.pnSUMSS_EUS:
                    nUS_Brake = 0
                    nTR = S.INICHANCE + 5000 * nUS_Brake + 5000 * nSS12
                    if 0 <= self.rand() * nTR * S.RAND / 10 <= 1:
                        SS[2][nX] = .1
            else:
                if SS[nCS][nX] == 0 and SUMSS[nCS] < self.pnSUMSS_EUS:   # no connection, and not yet saturation of all lines
                    nUS_Brake = 0   # Range 0 to 1, is inverse parameter of US strength
                    if brake:
                        nSS12 = (SS[nCS][nX] + SS[nCSD][nX]) / 10
                    nTR = S.INICHANCE + 5000 * nUS_Brake + 5000 * nSS12
                    if 0 <= self.rand() * nTR * S.RAND / 10 <= 1:
                        SS[nCS][nX] = .1   # When set = 0.1 'sensitivity' for LTP returns

    # -- PROCEDURE LINEDRAW --------------------------------------------------
    def LINEDRAW(self, nCS, nW, lWis, nV):
        g = self.g
        g.ForeColor = g.BackColor if lWis else (pnRood if nCS == 1 else pnBlauw)
        g.DrawWidth = INT(nW)   # DrawWidth is an integer property: VFP truncates
        if nW > 0.05:
            if nW < 1:
                g.DrawStyle = 2
                g.DrawWidth = 1
            g.Line(self.pnHOffSet, self.pnVOffSet + self.pnDist * (0 if nCS == 1 else int(self.SGM.NONQTY) - 1),
                   self.pnHPosNON - self.pnRad, nV)   # Line from MF to NON
            g.DrawStyle = 0

    # -- PROCEDURE GAUSS -----------------------------------------------------
    def GAUSS(self, nVOffSet, nHOffSet, nHeight, nDW):
        g = self.g
        g.DrawWidth = nDW
        nHeight2, nWidth, nTopHOffSet = 20, 16, 26
        for nX in range(1, 51):
            nS = INT(4 + nHeight * (INT(nHeight2 / 7) + 1) *
                     math.e ** (((-4 * math.log(2)) * (nX - nTopHOffSet) ** 2) / nWidth ** 2))
            g.PSet(nX + nHOffSet, nVOffSet - nS)

    # -- Events --------------------------------------------------------------
    def CBU_Click(self, ctl):   # SG_CBU.Click
        cCap = ctl.Caption
        if "CS1" in cCap:
            ctl.Caption = "CS1 OFF" if ctl.Caption == "CS1 ON" else "CS1 ON"
            ctl.ForeColor = pnRood if ctl.Caption == "CS1 ON" else pnWit
        elif "CS2" in cCap:
            ctl.Caption = "CS2 OFF" if ctl.Caption == "CS2 ON" else "CS2 ON"
            ctl.ForeColor = pnBlauw if ctl.Caption == "CS2 ON" else pnWit
        elif "INTERMIXED" in ctl.Tag:
            ctl.Caption = "COMPOUNDED"
            ctl.Tag = ctl.Caption
            self.SG_SP3.Value = 0
        elif "COMPOUNDED" in ctl.Tag:
            ctl.Caption = "INTERMIXED"
            ctl.Tag = ctl.Caption
            if self.SG_SP3.Value == 0:
                self.SG_SP3.Value = .1
        elif "TRACE" in cCap:
            ctl.Caption = "TRACE OFF" if ctl.Caption == "TRACE ON" else "TRACE ON"
        elif "BEAM" in cCap:
            ctl.Caption = "BEAM OFF" if ctl.Caption == "BEAM ON" else "BEAM ON"
        elif "METAB" in cCap:
            ctl.Caption = "METAB.BRAKE OFF" if ctl.Caption == "METAB.BRAKE ON" else "METAB.BRAKE ON"
        if "ON" in self.SG_CBU1.Caption and "ON" in self.SG_CBU2.Caption:
            self.SG_CBU3.Enabled = True
            self.SG_CBU3.Caption = self.SG_CBU3.Tag
        else:
            self.SG_CBU3.Enabled = False
            self.SG_CBU3.Caption = "---"
        self.flush()

    def CBD_MouseDown(self, ctl):   # SG_CBD.MouseDown
        self.commit_spinners()
        self.SetAll("ForeColor", pnZwart, "SG_CBD")
        cCap = ctl.Caption
        self.plRun = self.plAbort = False
        if cCap == "RUN":
            if self.running:
                return
            self.SetAll("Enabled", False, "SG_SP")
            self.SG_CBD2.Enabled = True
            self.SG_CBD2.Caption = "STOP"
            self.plRun = True
            self.g.Cls()
            if self.SG_SP10.Value == 0:
                self.DORUN(False)
            else:
                self.pcCMD = LTSTR(self.SG_SP10.Value)
                self.DEMO()
        elif cCap == "STOP":
            self.plStop = True
            self.SG_CBD1.Caption = "CONTINUE"
        elif cCap == "CONTINUE":
            if self.running:
                return
            self.plRun = True
            self.plStop = False
            self.DORUN(True)
        elif cCap == "ABORT":
            self.SG_CBD2.Enabled = False
            self.SetAll("Enabled", True, "SG_SP")
            self.plAbort = True
            self.SG_CBD1.Caption = "RUN"
        self.flush()

    def SP10_UpClick(self):   # SG_SP10.UpClick / DownClick: sets the demo values for demo x
        self.SG_CBD1.Caption = "RUN"
        self.pcCMD = LTSTR(self.SG_SP10.Value)
        self.SG_SP10.ToolTipText = SP10_TIPS[int(self.SG_SP10.Value)] if self.SG_SP10.Value else ""
        self.DEMO(True)
        self.flush()


# PROCEDURE TTText: tooltip of the Demo spinner
SP10_TIPS = [None,
             "Presentation of demo components.",
             "Showing thickening lines.",
             "Showing Gauss curves.",
             "Complete run, intermixed, trace off, showing the segregation process.",
             "Trace divergence demo with 10 NONs, random function enabled.",
             "Trace divergence demo with 10 NONs, random function disabled.",
             "'Transfer training' CS1->CS2->CS1 with M-BRAKE OFF.",
             "'Transfer training' CS1->CS2 with M-BRAKE ON.",
             "CS1 CS2 INTERMIXED with M-BRAKE ON.",
             "'Transfer training' CS1->CS2->CS1 with M-BRAKE ON," + pcCR + "running longer to watch 'erosion' of CS1,"
             + pcCR + "and quick resurgence of CS1 when activated again.",
             "'Transfer training' CS1->CS2->CS1 with M-BRAKE ON AND background noise.",
             "Interactive mode.",
             "CS1 CS2 COMPOUNDED with M-BRAKE ON AND Background noise.",
             "Blocking of CS1 after full training with CS2."]


# ----------------------------------------------------------------------------
# Demo panel: one button per pcCMD demo (as with 'DO segreg WITH .T.,"n"')
# Figures and page numbers according to the Zenodo version of the article
# (doi:10.5281/zenodo.17584844): page number = the number printed at the bottom of the page.
# ----------------------------------------------------------------------------
DEMOS = [
    ("1", "Demo 1 \u00b7 Fig. 1, p. 14\nComponents of the demo",
     "Presentation of the demo components: the start of a run (100 steps).\nArticle: Fig. 1, page 14."),
    ("2", "Demo 2 \u00b7 Fig. 2, p. 15\nThickening lines",
     "MF-NON lines thicken by LTP and the CF lines thicken when CFs start to fire (345 steps).\nArticle: Fig. 2, page 15."),
    ("3", "Demo 3 \u00b7 Fig. 3, p. 15\nCR curves (double peaks)",
     "The CR 'Gaussians' appear: both CSs trigger each other's CRs, the double peaks phenomenon (500 steps).\n"
     "Article: Fig. 3, page 15."),
    ("4", "Demo 4 \u00b7 Figs. 4, 5, p. 16\nComplete segregation run",
     "Complete run, intermixed, trace off: the slow segregation of CS1 and CS2 onto different nanoloops.\n"
     "Article: Figs. 4 and 5, page 16."),
    ("5", "Demo 5 \u00b7 Fig. 6, p. 18\nTraces, random factor on",
     "Trace divergence with 10 NONs, random factor enabled: the traces diverge.\nArticle: Fig. 6, page 18."),
    ("6", "Demo 6 \u00b7 Fig. 6, p. 18\nTraces, random factor off",
     "Trace divergence with 10 NONs, random factor disabled: no segregation, double peaks persist.\n"
     "Article: Fig. 6, page 18."),
    ("7", "Demo 7 \u00b7 Fig. 7, p. 19\nTransfer CS1>CS2>CS1",
     "'Transfer training' CS1 -> CS2 -> CS1 with the metabolic brake OFF: each time a complete takeover.\n"
     "Article: Fig. 7, page 19."),
    ("8", "Demo 8 \u00b7 Fig. 8a, p. 20\nTransfer, metab. brake on",
     "'Transfer training' CS1 -> CS2 with the metabolic brake ON: CS2 only about halves the CR power of CS1.\n"
     "Article: Fig. 8a, page 20."),
    ("9", "Demo 9 \u00b7 Figs. 8b, 8c, p. 20\nIntermixed, metab. brake on",
     "CS1 and CS2 intermixed with the metabolic brake ON: the transient double peaks are preserved.\n"
     "Article: Figs. 8b and 8c, page 20."),
    ("10", "Demo 10 \u00b7 text, p. 20\nErosion of CS1",
     "'Transfer training' CS1 -> CS2 -> CS1 with the metabolic brake ON, running longer to watch the 'erosion' "
     "of CS1, and the quick resurgence of CS1 when activated again.\nArticle: text on page 20 (no figure)."),
    ("11", "Demo 11 \u00b7 text, p. 20\nTransfer + background noise",
     "'Transfer training' CS1 -> CS2 -> CS1 with the metabolic brake ON and background noise: no more erosion.\n"
     "Article: text on page 20 (no figure)."),
    ("12", "Demo 12\nInteractive mode",
     "All controls visible; set the parameters (or a demo number) and click RUN.\n"
     "The screenshots in the article were taken in this mode."),
    ("13", "Demo 13 (not in the article)\nCompounded + noise",
     "CS1 and CS2 COMPOUNDED with the metabolic brake ON and background noise.\nNot shown in the article."),
    ("14", "Demo 14 (not in the article)\nCS2, then compound",
     "Pretraining with CS2 followed by 'simultaneous' COMPOUND training with CS1 and CS2 (blocking).\n"
     "Not shown in the article."),
    ("", "Normal mode (restart)",
     "Restarts the program in its normal mode (not called with a demo parameter)."),
]


class Shell:
    """Manages (re)starting the SEGREG form with or without a demo parameter."""

    SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0]

    def __init__(self, root, S, seed, speed=1.0):
        self.root, self.S, self.seed = root, S, seed
        self.speed = speed
        self.speed_buttons = {}
        self.panel = []
        self.app = None
        self.pending = None
        self.current = None

    def start(self, demo):
        if self.app:
            self.app.stop()
        for w in self.root.winfo_children():
            w.destroy()
        self.current = demo
        # Demo 12 was called in 'interactive' mode in the article ("12I"): all controls stay visible.
        self.app = Segreg(self.root, self.S, plCalled=bool(demo), pcCMD=demo, plIA=(demo == "12"), seed=self.seed)
        self.app.speed = self.speed
        self.app.on_width = self.layout
        self.build_panel()
        self.layout(self.app.Width)
        self.root.after(50, self.app.activate)

    def layout(self, w):
        S = self.S
        self.root.geometry("%dx%d" % (int((w + PANEL_W) * S), int(PNH * S)))
        for widget, l, t, ww, hh in self.panel:
            widget.place(x=int((w + l) * S), y=int(t * S), width=int(ww * S), height=int(hh * S))

    def build_panel(self):
        S, app = self.S, self.app
        self.panel = []
        n = len(DEMOS)
        left, top0, gap, speed_h = 6, 6, 3, 52
        h = (PNH - top0 - 6 - speed_h - gap * (n - 1)) / n
        for i, (cmd, cap, tip) in enumerate(DEMOS):
            active = (cmd == self.current)
            b = tk.Button(self.root, text=cap, takefocus=0, padx=1, pady=0,
                          font=app.tkfont("Arial", 7, True), wraplength=int((PANEL_W - 14) * S),
                          bg=hexc(pnGeel) if active else hexc(LABEL_BACK),
                          relief="sunken" if active else "raised",
                          command=lambda c=cmd: self.request(c))
            self.panel.append((b, left, top0 + i * (h + gap), PANEL_W - 10, h))
            self._tip(b, tip)

        # Playback speed, as with a video player
        y0 = top0 + n * (h + gap) + 2
        lbl = tk.Label(self.root, text="Speed", bg=hexc(pnGrijs), fg="white",
                       font=app.tkfont("Arial", 7, True), anchor="w")
        self.panel.append((lbl, left, y0, PANEL_W - 10, 14))
        self._tip(lbl, "Playback speed of runs and demos, as with a video player.\n"
                       "1x is the speed of the original program in Visual FoxPro 9.\n"
                       "Can be changed while a run is executing.")
        bw = (PANEL_W - 10) / 3
        self.speed_buttons = {}
        for k, sp in enumerate(self.SPEEDS):
            txt = ("%g" % sp).replace(".", ",") + "\u00d7"
            b = tk.Button(self.root, text=txt, takefocus=0, padx=0, pady=0,
                          font=app.tkfont("Arial", 7, True),
                          command=lambda sp=sp: self.set_speed(sp))
            self.panel.append((b, left + (k % 3) * bw, y0 + 15 + (k // 3) * 18, bw - 2, 17))
            self.speed_buttons[sp] = b
        self._mark_speed()

    def _tip(self, widget, tip):
        holder = type("H", (), {})()
        holder.app, holder.ToolTipText, holder.all_widgets = self.app, tip, (lambda w=widget: [w])
        ToolTip(holder)

    def set_speed(self, sp):
        self.speed = sp
        self.app.speed = sp       # takes effect immediately, also during a run
        self._mark_speed()

    def _mark_speed(self):
        for sp, b in self.speed_buttons.items():
            on = (sp == self.speed)
            b.config(bg=hexc(pnGeel) if on else hexc(LABEL_BACK), relief="sunken" if on else "raised")

    def request(self, demo):
        # The running form stops at its next DOEVENTS; the new one starts once its procedures have returned.
        self.pending = demo
        self.app.dead = True
        self.root.after(20, self._poll)

    def _poll(self):
        if self.pending is None:
            return
        if self.app.busy:
            self.root.after(30, self._poll)
            return
        demo, self.pending = self.pending, None
        self.start(demo)


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="SEGREG - Python version of segreg.prg")
    ap.add_argument("--scale", type=float, default=None,
                    help="scale factor (default: automatic, following the Windows DPI)")
    ap.add_argument("--seed", type=int, default=None, help="fixed seed for reproducible runs")
    ap.add_argument("--demo", default="", help="demo mode 1..14 (pcCMD)")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="playback speed, e.g. 0.5 = half speed (as with a video player)")
    args = ap.parse_args()
    if args.demo and args.demo not in [str(i) for i in range(1, 15)]:
        ap.error("--demo must be 1..14")

    if sys.platform == "win32":
        try:   # sharp rendering on high-DPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    root.title("SEGREG")
    root.configure(bg=hexc(pnGrijs))
    root.resizable(False, False)
    S = args.scale if args.scale else max(1.0, round(root.winfo_fpixels("1i") / 96.0 * 4) / 4)

    shell = Shell(root, S, args.seed, max(0.05, args.speed))
    shell.start(args.demo)

    def on_close():
        shell.app.closed = True
        shell.app.stop()
        try:
            root.destroy()
        except tk.TclError:
            pass

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        root.mainloop()
    except (SystemExit, tk.TclError):
        pass


if __name__ == "__main__":
    main()
