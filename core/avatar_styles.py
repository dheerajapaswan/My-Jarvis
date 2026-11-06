"""
core/avatar_styles.py - naye avatar: Reactor (JARVIS / Max) aur Aankhein (Riya).
config/api_keys.json mein "avatar_look": "auto" | "reactor" | "eyes" | "head"
"""
from __future__ import annotations

import math
import random
import time

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient


def _c(col, a):
    q = QColor(col)
    q.setAlpha(int(max(0.0, min(255.0, a))))
    return q


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return QColor(int(a.red() + (b.red() - a.red()) * t),
                  int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


def _ease(cur, tgt, dt, tau):
    return cur + (tgt - cur) * (1.0 - math.exp(-max(0.0, dt) / max(1e-3, tau)))


class _Base:
    SPAN = 2.0

    def __init__(self):
        self._t = 0.0
        self._amp = 0.0
        self._speaking = False
        self._muted = 0.0
        self._think = 0.0
        self._listen = 0.0
        self._blink = 0.0
        self._next_blink = 2.0
        self._gx = self._gy = 0.0
        self._tgx = self._tgy = 0.0
        self._next_gaze = 1.5
        self._glance_until = 0.0

    def glance(self, dx, dy, hold=1.1):
        self._tgx = max(-1.0, min(1.0, float(dx)))
        self._tgy = max(-1.0, min(1.0, float(dy)))
        self._glance_until = self._t + max(0.1, float(hold))

    def step(self, dt, amp, speaking=False, muted=False, state="", **_ignored):
        dt = max(0.0, min(0.1, float(dt)))
        self._t += dt
        st = (state or "").upper()
        self._speaking = bool(speaking)
        a = max(0.0, min(1.0, float(amp or 0.0)))
        self._amp = _ease(self._amp, a, dt, 0.05 if a > self._amp else 0.12)
        self._muted = _ease(self._muted, 1.0 if muted else 0.0, dt, 0.25)
        self._think = _ease(self._think, 1.0 if st in ("THINKING", "PROCESSING") else 0.0, dt, 0.25)
        listening = (st == "LISTENING") and not speaking and not muted
        self._listen = _ease(self._listen, (0.15 + a * 0.85) if listening else 0.0, dt, 0.15)
        self._next_blink -= dt
        if self._next_blink <= 0 and not muted:
            self._blink = 1.0
            self._next_blink = 2.2 + random.random() * 3.2
        self._blink = max(0.0, self._blink - dt * 7.0)
        if self._t > self._glance_until:
            self._next_gaze -= dt
            if self._next_gaze <= 0:
                if self._think > 0.5:
                    self._tgx, self._tgy = (0.55 if random.random() < .5 else -0.55), -0.6
                elif random.random() < 0.55:
                    self._tgx = self._tgy = 0.0
                else:
                    self._tgx = random.uniform(-0.6, 0.6)
                    self._tgy = random.uniform(-0.35, 0.35)
                self._next_gaze = 1.2 + random.random() * 2.4
        self._gx = _ease(self._gx, self._tgx, dt, 0.09)
        self._gy = _ease(self._gy, self._tgy, dt, 0.09)

    def _eye_open(self):
        b = math.sin(self._blink * math.pi) if self._blink > 0 else 0.0
        return max(0.04, min(1.0, (1 - b) * (1 - 0.82 * self._muted)))

    @staticmethod
    def _aura(p, cx, cy, rad, col, a):
        g = QRadialGradient(cx, cy, rad)
        g.setColorAt(0.0, _c(col, a))
        g.setColorAt(1.0, _c(col, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QRectF(cx - rad, cy - rad, rad * 2, rad * 2))


class ReactorAvatar(_Base):
    _RINGS = ((0.98, 10, 0.35, 0.040, 0.35),
              (0.80, 6, 0.50, 0.062, -0.60),
              (0.62, 14, 0.30, 0.028, 0.90))

    def __init__(self):
        super().__init__()
        self._spin = 0.0
        self._comet = 0.0

    def step(self, dt, amp, speaking=False, muted=False, state="", **kw):
        super().step(dt, amp, speaking=speaking, muted=muted, state=state, **kw)
        dt = max(0.0, min(0.1, float(dt)))
        self._spin += dt * (1 + self._think * 4) * (1 - self._muted * 0.95)
        self._comet += dt * 5

    def paint(self, p, cx, cy, r, primary, accent, bg=None):
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        R = r * 0.78
        energy = (self._amp if self._speaking else 0.0) + self._listen * 0.6
        t = self._t
        self._aura(p, cx, cy, r * 1.25, primary, 26 + 46 * energy)
        for i in range(96):
            a = i / 96 * math.tau + self._spin * 0.05
            long_ = (i % 8 == 0)
            r1, r2 = R * 1.12, R * (1.2 if long_ else 1.16)
            p.setPen(QPen(_c(primary, 140 if long_ else 56), max(1.0, r * (0.010 if long_ else 0.005))))
            p.drawLine(QPointF(cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                       QPointF(cx + math.cos(a) * r2, cy + math.sin(a) * r2))
        for k, (rr, n, gap, w, sp) in enumerate(self._RINGS):
            rad = R * rr * (1 + energy * 0.05 * math.sin(t * 9 + k))
            box = QRectF(cx - rad, cy - rad, rad * 2, rad * 2)
            seg = 360.0 / n
            for i in range(n):
                a0 = i * seg + math.degrees(self._spin * sp)
                lit = 0.35 + 0.65 * max(0.0, min(1.0, energy * 1.3 * (0.6 + 0.4 * math.sin(t * 6 + i * 1.7))))
                pen = QPen(_c(primary, 255 * lit * (1 - self._muted * 0.5)), max(1.5, r * w))
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                p.setPen(pen)
                p.drawArc(box, int(a0 * 16), int(seg * (1 - gap) * 16))
        if self._think > 0.02:
            rad = R * 1.04
            box = QRectF(cx - rad, cy - rad, rad * 2, rad * 2)
            head = math.degrees(self._comet)
            for i in range(24):
                pen = QPen(_c(accent, 230 * self._think * (1 - i / 24)), max(1.5, r * 0.018))
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                p.setPen(pen)
                p.drawArc(box, int((head - i * 2.3) * 16), int(2.4 * 16))
        cr = R * (0.26 + energy * 0.12)
        g = QRadialGradient(cx, cy, cr * 1.9)
        white = QColor(255, 255, 255)
        g.setColorAt(0.0, _c(_mix(accent, white, 0.75), 245 - self._muted * 130))
        g.setColorAt(0.35, _c(accent, 190 - self._muted * 100))
        g.setColorAt(1.0, _c(accent, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QRectF(cx - cr * 1.9, cy - cr * 1.9, cr * 3.8, cr * 3.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(_c(accent, 180), max(1.0, r * 0.008)))
        p.drawEllipse(QRectF(cx - cr, cy - cr, cr * 2, cr * 2))
        if self._listen > 0.02:
            ph = (t * 0.6) % 1.0
            rad = R * (0.3 + ph * 1.0)
            p.setPen(QPen(_c(accent, 255 * (1 - ph) * min(1.0, self._listen * 1.6)), max(1.0, r * 0.008)))
            p.drawEllipse(QRectF(cx - rad, cy - rad, rad * 2, rad * 2))
        p.restore()


class EyesAvatar(_Base):
    def paint(self, p, cx, cy, r, primary, accent, bg=None):
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        U = r * 2.0
        t = self._t
        amp = self._amp if self._speaking else 0.0
        self._aura(p, cx, cy, r * 1.2, primary, 24 + 36 * amp + 40 * self._listen)
        opn = self._eye_open()
        bob = math.sin(t * 1.6) * U * 0.006 + amp * U * 0.01
        ew, eh = U * 0.19, U * 0.25
        for sgn in (-1, 1):
            ex = cx + sgn * U * 0.17 + self._gx * U * 0.03
            ey = cy - U * 0.08 + self._gy * U * 0.02 + bob
            hh = max(U * 0.012, eh * opn)
            p.setPen(Qt.PenStyle.NoPen)
            for k, a in ((3, 22), (2, 40), (1, 70)):
                pad = U * 0.012 * k
                p.setBrush(_c(primary, a))
                p.drawRoundedRect(QRectF(ex - ew / 2 - pad, ey - hh / 2 - pad, ew + pad * 2, hh + pad * 2),
                                  ew * 0.45 + pad, min(ew * 0.45, hh / 2) + pad)
            p.setBrush(_c(primary, 245))
            p.drawRoundedRect(QRectF(ex - ew / 2, ey - hh / 2, ew, hh), ew * 0.45, min(ew * 0.45, hh / 2))
            if opn > 0.4:
                p.setBrush(QColor(255, 255, 255, 190))
                hx = ex + self._gx * ew * 0.22 - ew * 0.12
                hy = ey + self._gy * hh * 0.2 - hh * 0.18
                rad = ew * 0.11
                p.drawEllipse(QRectF(hx - rad, hy - rad, rad * 2, rad * 2))
        my = cy + U * 0.17 + bob
        mw = U * 0.09
        if amp > 0.04:
            mh = U * (0.015 + amp * 0.075)
            mwid = mw * (0.75 - amp * 0.15)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_c(primary, 230))
            p.drawEllipse(QRectF(cx - mwid, my - mh, mwid * 2, mh * 2))
        else:
            pen = QPen(_c(primary, 240), max(1.5, U * 0.022))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            if self._muted > 0.5:
                p.drawLine(QPointF(cx - mw * 0.6, my), QPointF(cx + mw * 0.6, my))
            else:
                rad = mw * 0.9
                ccy = my - rad * 0.85
                p.drawArc(QRectF(cx - rad, ccy - rad, rad * 2, rad * 2), -140 * 16, 100 * 16)
        if self._think > 0.05:
            p.setPen(Qt.PenStyle.NoPen)
            for k in range(3):
                a = max(0.0, min(1.0, math.sin(t * 5 - k * 0.8))) * self._think
                p.setBrush(_c(accent, 255 * a))
                rad = U * (0.012 + k * 0.004)
                x, y = cx + U * (0.24 + k * 0.05), cy - U * (0.30 + k * 0.03)
                p.drawEllipse(QRectF(x - rad, y - rad, rad * 2, rad * 2))
        if self._listen > 0.02:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_c(accent, 170))
            for k in range(9):
                bh = U * (0.01 + self._listen * 0.12 * abs(math.sin(t * 7 + k * 0.9)))
                p.drawRect(QRectF(cx + (k - 4) * U * 0.03 - U * 0.007, cy + U * 0.33 - bh / 2, U * 0.014, bh))
        p.restore()


class SwitchingAvatar:
    def __init__(self, holo_cls=None):
        self._holo_cls = holo_cls
        self._holo = None
        self._reactor = ReactorAvatar()
        self._eyes = EyesAvatar()
        self._cur = self._reactor
        self._checked = 0.0
        self._pick(force=True)

    def _want(self):
        try:
            from memory.config_manager import load_api_keys, get_plugin_setting
            look = str(load_api_keys().get("avatar_look", "auto")).strip().lower()
            if look in ("reactor", "eyes", "head"):
                return look
            return "eyes" if get_plugin_setting("persona_switch", "current", "") == "riya" else "reactor"
        except Exception:
            return "reactor"

    def _pick(self, force=False):
        now = time.monotonic()
        if not force and now - self._checked < 1.5:
            return
        self._checked = now
        want = self._want()
        if want == "head" and self._holo_cls is not None:
            if self._holo is None:
                try:
                    self._holo = self._holo_cls()
                except Exception:
                    self._holo = None
            self._cur = self._holo or self._reactor
        else:
            self._cur = self._eyes if want == "eyes" else self._reactor

    @property
    def SPAN(self):
        return getattr(self._cur, "SPAN", 2.0)

    def step(self, *a, **kw):
        self._pick()
        return self._cur.step(*a, **kw)

    def paint(self, *a, **kw):
        return self._cur.paint(*a, **kw)

    def glance(self, *a, **kw):
        return self._cur.glance(*a, **kw)

    def __getattr__(self, name):
        return getattr(self._cur, name)
