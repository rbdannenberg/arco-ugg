// ugen.cpp -- base for unit generators

#include "stdlib.h"
#include "assert.h"
#include "ugen.h"

long ugg_block_count = 1;

Table *table_create(int len)
{
    // actual array size will be len + 1
    long bytes = sizeof(Table) + (len - 1) * sizeof(float);
    Table *table = (Table *) malloc(bytes);
    table->len = len + 1;
    return table;
}


double uniform()
{
    return ((double) rand()) / RAND_MAX;
}


Ugen::Ugen()
{ 
    block_count = ugg_block_count;
}

Ugen_outa::Ugen_outa()
{
}


sample *Ugen_outa::get_outs()
{
    return outs;
}


sample Ugen_outa::get_out()
{
    assert(false);
    return NULL;
}


Ugen_outb::Ugen_outb()
{
}


sample *Ugen_outb::get_outs()
{
    assert(false);
    return NULL;
}


sample Ugen_outb::get_out()
{
    return out;
}
