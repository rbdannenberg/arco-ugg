// ugen.cpp - superclass
//
// Roger B. Dannenberg
// Mar 2018

#include "arcocommon.h"
#include "mem.h"

void *Ugen::operator new(size_t size)
{
    return o2x_alloc(size);
}

void Ugen::operator delete(void *ptr)
{
    o2x_free(ptr);
}

void Ugen_array::destroy()
{
    for (int i = 0; i < array.length; i++) {
        delete (*this)[i];
    }
}

