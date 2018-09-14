# ugenv.py -- envelope functions and unit generators

from Ugen import *

def decay(pamp, ptime):
    state = First("state", pamp)
    dursamples = Var("dursamples", Umax(Ugen(1), ptime * Ugen("AR")))
    decay = Var("decay", Upow(Ugen(0.001), Udiv(Ugen(1.0), dursamples)))
    Next(state, state * decay)
    state.use_output_rate()
    pamp.update(state, pamp)
    return state


def ug_decay():
    ugg_begin("Decay")
    pamp = Param("amp")
    ptime = Param("time")
    ugg_generate(ARGEN(CR, CR), [pamp, ptime], decay(pamp, ptime))

