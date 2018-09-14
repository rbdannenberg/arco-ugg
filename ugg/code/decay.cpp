// decay implementations

#include "ugen.h"
#include "decay.h"

Decay_cc_a::Decay_cc_a(sample amp, sample time)
{
    block_count = 0;
    this->amp = amp;
    this->time = time;
    dursamples = fmax(1, (time * AR));
    decay = (amp / dursamples);
    state = amp;
}

void Decay_cc_a::run(long block_num)
{
    block_count = block_num;
    for (int i = 0; i < BL; i++) {
        outs[i] = state;
        sample state_next = fmax((state - decay), 0);
        state = state_next;
    }
}
void Decay_cc_a::set_amp(sample amp) {
    state = amp;
}
