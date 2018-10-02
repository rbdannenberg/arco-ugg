# ugenv.py -- envelope functions and unit generators

from Ugen import *

def decay(pamp, ptime):
    state = First("state", pamp)
    dursamples = Var("dursamples", Umax(Ugen(1), ptime * Ugen("AR")))
    decay = Var("decay", pamp / dursamples)
    Next(state, Umax(state - decay, 0))
    state.use_output_rate()
    pamp.update(state, pamp)
    return state


def ug_decay():
    ugg_begin("Decay")
    pamp = Param("amp")
    ptime = Param("time")
    ugg_generate(ARGEN(CR, CR), [pamp, ptime], decay(pamp, ptime))

