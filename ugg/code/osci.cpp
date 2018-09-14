// osci implementations

#include "ugen.h"
#include "osci.h"

Osci_acc_a::Osci_acc_a(Ugen *hz, double phase, Table_ptr table)
{
    block_count = 0;
    this->table = table;
    this->phase = phase;
    table_len = table_len(table);
    this->hz = hz;
    indexf = (phase * table_len);
}

void Osci_acc_a::run(long block_num)
{
    if (hz->block_count < block_num) {
        hz->run(block_num);
    }
    block_count = block_num;
    sample *hz_samps = hz->get_outs();
    for (int i = 0; i < BL; i++) {
        int index = int(indexf);
        sample x1 = tblget(table, index);
        outs[i] = (x1 + ((indexf - index) * (tblget(table, (index + 1)) - x1)));
        double indexf_next = phase_wrap((indexf + ((hz_samps[i] * table_len) * AR_RECIP)), table_len);
        indexf = indexf_next;
    }
}

Osci_bcc_a::Osci_bcc_a(Ugen *hz, double phase, Table_ptr table)
{
    block_count = 0;
    this->table = table;
    this->phase = phase;
    table_len = table_len(table);
    this->hz = hz;
    indexf = (phase * table_len);
}

void Osci_bcc_a::run(long block_num)
{
    if (hz->block_count < block_num) {
        hz->run(block_num);
    }
    block_count = block_num;
    sample t1 = ((hz->get_out() * table_len) * AR_RECIP);
    for (int i = 0; i < BL; i++) {
        int index = int(indexf);
        sample x1 = tblget(table, index);
        outs[i] = (x1 + ((indexf - index) * (tblget(table, (index + 1)) - x1)));
        double indexf_next = phase_wrap((indexf + t1), table_len);
        indexf = indexf_next;
    }
}

Osci_ccc_a::Osci_ccc_a(double hz, double phase, Table_ptr table)
{
    block_count = 0;
    this->table = table;
    this->phase = phase;
    table_len = table_len(table);
    this->hz = hz;
    t2 = ((hz * table_len) * AR_RECIP);
    indexf = (phase * table_len);
}

void Osci_ccc_a::run(long block_num)
{
    block_count = block_num;
    for (int i = 0; i < BL; i++) {
        int index = int(indexf);
        sample x1 = tblget(table, index);
        outs[i] = (x1 + ((indexf - index) * (tblget(table, (index + 1)) - x1)));
        double indexf_next = phase_wrap((indexf + t2), table_len);
        indexf = indexf_next;
    }
}
