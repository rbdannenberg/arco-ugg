# ugmath.py -- simply math unit generators on signals

from Ugen import *


def ug_mult():
    ugg_begin("Mult")
    pa = Param("a")
    pb = Param("b")
    ugg_generate(FILTER(AR+BR, AR+BR+CR), [pa, pb], pa * pb, commutative=True)


def ug_add():
    ugg_begin("Add")
    pa = Param("a")
    pb = Param("b")
    ugg_generate(FILTER(AR+BR, AR+BR+CR), [pa, pb], pa + pb, commutative=True)
