/* mem.c -- fast memory allocation/deallocation module */

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
#define O2XM_DEBUG 1

#include <stdio.h>
#include <string.h>
#include "o2.h"
#include "mem.h"
#include <libkern/OSAtomic.h>

#ifdef O2XM_DEBUG
#define arc_error printf
#endif

#define ARC_MEM_CHUNK_SIZE (1 << 16)
#define MAX(x, y) ((x) > (y) ? (x) : (y))


static O2x_node_ptr linear_free[MAX_LINEAR_BYTES / ALIGN];
static O2x_node_ptr exponential_free[LOG2_MAX_EXPONENTIAL_BYTES];

/* state of the heap */
static int64_t chunk_remaining;
static int64_t total_allocated;
static int mallocp;
static char *chunk;


#ifdef O2XM_DEBUG
    static void *low_address; // the lowest address we have seen
    static void *high_address;// the highest address we have seen

    static void check(void *ptr, int64_t size);
    static void check_address(char *ptr, int64_t size);
#else
    why is not AM_DEBUG defined?
#endif


// return log of actual block size on exponential free list
static int power_of_2_block_size(int64_t size)
{
    int log = LOG2_MAX_LINEAR_BYTES + 1;
    while (size > (1 << log)) log++;
    return log;
}


// returns a pointer to the sublist for a given size.
static O2x_node_ptr *head_ptr_for_size(int64_t *size)
{
    *size = ALIGNUP(*size);
    long index = ALIGNED_COUNT(*size);
    if (index <= 0) {
        return NULL;
    } else if (index < (MAX_LINEAR_BYTES / ALIGN)) {
        return &(linear_free[index]);
    } else if (index <= ((1 << LOG2_MAX_EXPONENTIAL_BYTES) / ALIGN)) {
        int log = power_of_2_block_size(*size);
        *size = 1 << log;
        return &(exponential_free[log]);
    } else {
        return NULL;
    }
}


void o2x_mem_init(char *first_chunk, int64_t size, int mp)
{
    memset((void *) linear_free, 0, sizeof(linear_free));
    memset((void *) exponential_free, 0, sizeof(exponential_free));
    chunk = first_chunk;
#ifdef AM_DEBUG
    low_address = chunk;
    high_address = chunk;
#endif
    mallocp = mp;
    chunk_remaining = size;
    total_allocated = 0;
}


void *o2x_alloc(int64_t size)
{
    // realsize is within 8 bytes of requested size. When debugging,
    // write a magic token after realsize to allow future checks for 
    // stray writes into heap memory outside of allocated blocks
    int64_t realsize = ALIGNUP(size) + sizeof(int64_t); // room for length
#   ifdef AM_DEBUG
        // room to store overwrite area
        realsize += 8;
#   endif
    // find what really gets allocated. Large blocks especially 
    // are rounded up to a power of two.
    O2x_node_ptr *p = head_ptr_for_size(&realsize);
    if (!p) {
#       ifdef AM_DEBUG
            arc_error("someone is allocating %lld bytes\n", size);
#       endif
        printf("Warning: o2x_alloc -- return NULL 1\n");
        return NULL;
    }

    char *result = (char *) OSAtomicDequeue((OSQueueHead *) p, 0);
    if (result) {
        goto gotit;
    }
    if (chunk_remaining < realsize) {
        // note that we throw away remaining chunk if there isn't enough
        int64_t chunksize = MAX(realsize, ARC_MEM_CHUNK_SIZE);
        if (!mallocp ||
            !(chunk = (char *) o2_malloc(chunksize))) {
            chunk_remaining = 0;
            printf("Warning: o2x_alloc -- return NULL 2\n");
            return NULL; // can't allocate a chunk
        }
        chunk_remaining = chunksize;
    }
    result = chunk;
    *(int64_t *)result = realsize; // store requested size in first 8 bytes
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
    *(int64_t *)(result + realsize) = 0xBADCAFE8DEADBEEF;
#endif
    return result + 8;
}


#ifdef AM_DEBUG

void check(void *ptr, int64_t size)
{
    int64_t realsize = ALIGNUP(size);
    char *block = (char *)ptr;
    if (*(int64_t *)(block + realsize) != 0xBADCAFE8DEADBEEF)
        arc_error("block was overwritten beyond realsize %lld: %p\n",
                   realsize, ptr);
    block -= 8;
    if (*(int64_t *)block != size)
        arc_error("block size mismatch: %p->%lld instead of %lld\n",
                   block, *(int64_t *)block, size);
}
#endif


void o2x_free(void *ptr)
{
    if (!ptr) {
        printf("o2x_free NULL ignored\n");
        return;
    }
    int64_t realsize = ((int64_t *)ptr)[-1];
    if (realsize == 0) {
        printf("Arc_mem size 0\n");
        return;
    }
    char *block = (char *)ptr;
    block -= sizeof(realsize);
#ifdef AM_DEBUG
    check(ptr, realsize);
#endif
    // head_ptr_for_size can round up realsize
    O2x_node_ptr *head_ptr = head_ptr_for_size(&realsize);
    total_allocated -= realsize;
    OSAtomicEnqueue((OSQueueHead *) head_ptr, block, 0);
}

