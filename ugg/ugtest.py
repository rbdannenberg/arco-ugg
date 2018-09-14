# ugtest.py -- some test code

# plan: 
#    create osci_acc_a
#           decay_cc_a
#           mult_aa_a
#    make a little synthesizer
#    write a little mapper to take MIDI in and map to
#      calls on methods:
#        note_on -> set osc frequency, set decay amplitude
#

from Ugen import *
from ugosc import *
from ugenv import *
from ugmath import *
from cmake import write_cmake_file

def math_test():
    ugg_begin("Math")
    px = Param("x")
    py = Param("y")
    pz = Param("z")
    Var("yval", py)
    math = Var("temp", (px + "yval") * pz)
    # print("Ugen List: ", math.get_ugen_list())

    math.print_tree()
    print()
    ugg_write([AR, CR, AR], [px, py, pz], math, AR)
    ugg_write([AR, BR, BR], [px, py, pz], math, AR)
    ugg_write([AR, AR, AR], [px, py, pz], math, AR)
    ugg_write([BR, BR, BR], [px, py, pz], math, BR)


# a component that does a simple smoothing of an input signal
#
def smooth(x):
    sm = First(make_temp_name(), 0)
    Next(sm, sm * 0.9 + x * 0.1)
    return sm


def smooth_test():
    ugg_begin("Smooth")
    px = Param("x")
    ugg_write([BR], [px], smooth(px), BR)

# ugg_begin("Osc")
# sine_table = Ugen("sine_table")
# pfreq = Param("freq")
# phase_incr = pfreq * Ugen("SR_RECIP")
# indexf = First("indexf", 0)
# index = Var("index", Uint(indexf))
# x1 = Var("x1", sine_table[index])
# Next(indexf, Ufmodf(indexf + phase_incr, Ugen("TABLE_LEN")))
# osc = x1 + (indexf - index) * (sine_table[index + 1] - x1)
# indexf.use_output_rate()
# phase_incr.use_non_interpolated()
# osc.print_tree()
# print()
# ugg_write([CR], [pfreq], osc, AR)
# ugg_write([BR], [pfreq], osc, AR)

# ---------

# def oscf(pfreq):
#     sine_table = Ugen("sine_table")
#     phase_incr = pfreq * Ugen("SR_RECIP")
#     indexf = First("indexf", 0)
#     index = Var("index", Uint(indexf))
#     x1 = Var("x1", sine_table[index])
#     Next(indexf, Ufmodf(indexf + phase_incr, Ugen("TABLE_LEN")))
#     osc = x1 + (indexf - index) * (sine_table[index + 1] - x1)
#     indexf.use_output_rate()
#     phase_incr.use_non_interpolated()
#     return osc


# ugg_begin("Osc")
# pfreq = Param("freq")
# ugg_write([CR], [pfreq], oscf(pfreq), AR)
# ugg_write([BR], [pfreq], oscf(pfreq), AR)

# ugg_write([BR], [pfreq], oscf(smooth(pfreq)), AR)


ug_osci()
ug_decay()
ug_add()
ug_mult()
write_cmake_file()

# ugg_begin("Phasor")
# freq = Param("freq")
# phase = First("phase", 0, "double")
# phase.use_output_rate()
# Next(phase, Ufmod(phase + freq / SR, 1))
# ugg_write([CR], [freq], phase, AR)

# test

# def foo():
#     print(123)


print("test 1")
expr = Ugen(100) + Ugen(200)
expr.print_tree()

print("test 2")
expr = Ugen(100) + Ugen(200) + 5 + Param("input")
expr.print_tree()
print(expr.gen_code())
# print_ugens("Ugen List", expr.get_ugen_list())
