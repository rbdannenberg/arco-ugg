/* mem.cpp -- fast memory allocation/deallocation module */

/* Allocate large chunks of memory using malloc.  From the chunks,
   allocate memory as needed on long-word boundaries.  Memory is
   freed by linking memory onto a freelist.  An array of freelists,
   one for each size, is maintained and checked before going to the
   chunk for more memory.  
 */
/*
#include "stddef.h"
#include <stdlib.h>
#include "tonalcppext.h"
#include "os.h"
#include "error.h"
#include "tonalmem.h"
#include "zone.h"
#include <stdio.h>
#include <string.h>
#include "assert.h"
*/
#define AM_DEBUG 1

#include <string.h>
#include <iostream>
#include "arcocommon.h"
#include "mem.h"
#include <libkern/OSAtomic.h>

using namespace std;

#ifdef AM_DEBUG
#define arc_error printf
#endif

#define ARC_MEM_CHUNK_SIZE (1 << 16)
#define MAX(x, y) ((x) > (y) ? (x) : (y))


Node_ptr Arc_mem::linear_free[MAX_LINEAR_BYTES / ALIGN];
Node_ptr Arc_mem::exponential_free[LOG2_MAX_EXPONENTIAL_BYTES];


void Arc_mem::class_init()
{
    memset((void *) linear_free, 0, sizeof(linear_free));
    memset((void *) exponential_free, 0, sizeof(exponential_free));
}


void Arc_mem::init(char *first_chunk, int64 size, bool mp)
{
    chunk = first_chunk;
#ifdef AM_DEBUG
    low_address = chunk;
    high_address = chunk;
#endif
    mallocp = mp;
    chunk_remaining = size;
    total_allocated = 0;
}


// return log of actual block size on exponential free list
int Arc_mem::power_of_2_block_size(int64 size)
{
    int log = LOG2_MAX_LINEAR_BYTES + 1;
    while (size > (1 << log)) log++;
    return log;
}


void *Arc_mem::alloc(int64 size)
{
    // realsize is within 8 bytes of requested size. When debugging,
    // write a magic token after realsize to allow future checks for 
    // stray writes into heap memory outside of allocated blocks
    int64 realsize = ALIGNUP(size) + sizeof(int64); // room for length
#   ifdef AM_DEBUG
        // room to store overwrite area
        realsize += 8;
#   endif
    // find what really gets allocated. Large blocks especially 
    // are rounded up to a power of two.
    Node_ptr *p = head_ptr_for_size(realsize);
    if (!p) {
#       ifdef AM_DEBUG
            arc_error("someone is allocating %lld bytes\n", size);
#       endif
        cout << "Warning: Arc_mem::alloc -- return NULL 1" << endl;
        return NULL;
    }

    char *result = (char *) OSAtomicDequeue(p, 0);
    if (result) {
        goto gotit;
    }
    if (chunk_remaining < realsize) {
        // note that we throw away remaining chunk if there isn't enough
        int64 chunksize = MAX(realsize, ARC_MEM_CHUNK_SIZE);
        if (!mallocp ||
            !(chunk = (char *) o2_malloc(chunksize))) {
            chunk_remaining = 0;
            cout << "Warning: Arc_mem::get -- return NULL 2" << endl;
            return NULL; // can't allocate a chunk
        }
        chunk_remaining = chunksize;
    }
    result = chunk;
    *(int64 *)result = realsize; // store requested size in first 8 bytes
    chunk += realsize;
    chunk_remaining -= realsize;
#ifdef AM_DEBUG
    if (result < low_address) low_address = result;
    if (result + realsize > high_address) high_address = result + realsize;
#endif
 gotit:
    total_allocated += realsize;
    
#ifdef AM_DEBUG
    realsize -= 8;
    *(int64 *)(result + realsize) = 0xBADCAFE8DEADBEEF;
#endif
    return result + 8;
}


#ifdef AM_DEBUG

void Arc_mem::check(void *ptr, int64 size)
{
    int64 realsize = ALIGNUP(size);
    char *block = (char *)ptr;
    if (*(int64 *)(block + realsize) != 0xBADCAFE8DEADBEEF)
        arc_error("block was overwritten beyond realsize %lld: %p\n",
                   realsize, ptr);
    block -= 8;
    if (*(int64 *)block != size)
        arc_error("block size mismatch: %p->%lld instead of %lld\n",
                   block, *(int64 *)block, size);
}
#endif


void Arc_mem::free(void *ptr)
{
    if (!ptr) {
        cout << "Arc_mem free NULL ignored" << endl;
        return;
    }
    int64 realsize = ((int64 *)ptr)[-1];
    if (realsize == 0) {
        cout << "Arc_mem size 0" << endl;
        return;
    }
    char *block = (char *)ptr;
    block -= sizeof(realsize);
#ifdef AM_DEBUG
    check(ptr, realsize);
#endif
    // head_ptr_for_size can round up realsize
    Node_ptr *head_ptr = head_ptr_for_size(realsize);
    total_allocated -= realsize;
    OSAtomicEnqueue(head_ptr, block, 0);
}

Arc_mem arc_mem;
