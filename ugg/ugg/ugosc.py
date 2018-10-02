# ugosc.py -- oscillator functions and unit generators

from Ugen import *

def osci(phz, pphase, ptable):
    table_len = Var("table_len", Utable_len(ptable), "int")
    phase_incr = phz *  table_len * Ugen("AR_RECIP")
    indexf = First("indexf", pphase * table_len)
    index = Var("index", Uint(indexf), "int")
    x1 = Var("x1", ptable[index])
    osc = x1 + (indexf - index) * (ptable[index + 1] - x1)
    Next(indexf, Uphasewrap(indexf + phase_incr, table_len))
    indexf.use_output_rate()
    phase_incr.use_non_interpolated() 
    return osc 


def ug_osci():
    ugg_begin("Osci")
    phz = Param("hz", "double")
    pphase = Param("phase", "double")
    ptable = Param("table", "Table_ptr")
    rates = ARGEN(AR+BR+CR, CR, CR)
    print("ug_osci", rates)
    ugg_generate(rates, [phz, pphase, ptable], 
                 osci(phz, pphase, ptable))
