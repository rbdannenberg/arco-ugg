// mult implementations

#include "ugen.h"
#include "mult.h"

Mult_aa_a::Mult_aa_a(Ugen *a, Ugen *b)
{
    block_count = 0;
    this->a = a;
    this->b = b;
}

void Mult_aa_a::run(long block_num)
{
    if (a->block_count < block_num) {
        a->run(block_num);
    }
    if (b->block_count < block_num) {
        b->run(block_num);
    }
    block_count = block_num;
    sample *a_samps = a->get_outs();
    sample *b_samps = b->get_outs();
    for (int i = 0; i < BL; i++) {
        outs[i] = (a_samps[i] * b_samps[i]);
    }
}

Mult_ab_a::Mult_ab_a(Ugen *a, Ugen *b)
{
    block_count = 0;
    this->a = a;
    this->b = b;
    b_arate = 0;
}

void Mult_ab_a::run(long block_num)
{
    if (a->block_count < block_num) {
        a->run(block_num);
    }
    if (b->block_count < block_num) {
        b->run(block_num);
    }
    block_count = block_num;
    sample *a_samps = a->get_outs();
    sample b_step = (b->get_out() - b_arate) * BR_RECIP;
    for (int i = 0; i < BL; i++) {
        outs[i] = (a_samps[i] * b_arate);
            b_arate += b_step;
    }
}

Mult_bb_b::Mult_bb_b(Ugen *a, Ugen *b)
{
    block_count = 0;
    this->a = a;
    this->b = b;
}

void Mult_bb_b::run(long block_num)
{
    if (a->block_count < block_num) {
        a->run(block_num);
    }
    if (b->block_count < block_num) {
        b->run(block_num);
    }
    block_count = block_num;
    out = (a->get_out() * b->get_out());
}
