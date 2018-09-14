// synth.h - synth class
//
// Roger B. Dannenberg
// Mar 2018

#include "arcocommon.h"

typedef class Synth {
    Instr_ptr *instruments;
    int instruments_len;
    int num_instrs;
    int id;
    Synth(int len) {
        num_instrs = 0;
        instruments_len = len;
        int bytes = len * sizeof(Instr_ptr);
        instruments = ug_alloc(bytes);
        bzero(instruments, bytes);
    }
    Instr_ptr lookup(uint32_t id) { return instruments[id >> 16]; }
    Ugen_ptr ugen(uint32_t id) { return lookup(id)->lookup(id & 0xFFFF); }
    Instr_ptr create_instr(uint32_t id, int len) {
        Instr_ptr instr = new Instr(len);
        Instr_ptr existing = lookup(id);
        if (existing) {
            delete existing;
        }
        instruments[id >> 16] = instr;
    }
} Synth_ptr;


