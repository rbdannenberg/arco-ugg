/* mem.h */

/* Free memory will consist of a bunch of free lists organized by size.
   Allocate by removing from head of list. Free by pushing back on list.
   
   If a list is empty, add to it from a large block of memory.
   
   To support larger object sizes, there are two free lists: a linear
   list with blocks in increments of 8, and an exponential list with
   block sizes that are powers of 2.
   
   The linear list block sizes go up to MAX_LINEAR_BYTES.
 */

#define MEM_H

#ifdef __cplusplus
extern "C" {
#endif

#define O2XM_DEBUG 1

/* how many bytes in the largest node managed in free_list array */
#define ALIGN 8
#define ALIGN_log2 3
#define ALIGNUP(s) ( ((s)+(ALIGN-1)) & ~(ALIGN-1) )
#define ALIGNED_COUNT(s) ( (((s)-1) >> ALIGN_log2) + 1  )
#define LOG2_MAX_LINEAR_BYTES 12 // up to 4KB chunks
#define MAX_LINEAR_BYTES (1 << LOG2_MAX_LINEAR_BYTES)
#define LOG2_MAX_EXPONENTIAL_BYTES 22

// here's what memory blocks look like to this module

typedef struct O2x_node_struct {
    int64_t length;
    // the base address seen by the client is here:
    struct Node_struct *next;  // client can overwrite this pointer
    char filler[8];            // actual size is variable
} O2x_node, *O2x_node_ptr;


void o2x_mem_init(char *first_chunk, int64_t size, int mallocp);
void *o2x_alloc(int64_t size);
void o2x_free(void *ptr);

#ifdef __cplusplus
}
#endif
