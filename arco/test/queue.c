/* queue.c -- non-blocking queue
 */
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <libkern/OSAtomic.h>
#include "o2.h"
#include "mem.h"
#include "queue.h"

#ifdef WIN32
#define bzero(addr, siz) memset(addr, 0, siz)
#endif

void o2x_msg_queue_init(o2x_msg_queue_ptr queue)
{
    QUEUE_INIT(queue->incoming);
    queue->pending = NULL;
}


o2_message_ptr o2x_msg_dequeue(o2x_msg_queue_ptr queue)
{
    o2_message_ptr tmp = NULL;
    if (!queue->pending) {
        o2_message_ptr all = QUEUE_GET_MSGS(queue->incoming);
        // store zero if nothing has changed
        while (!OSAtomicCompareAndSwapPtrBarrier(all, NULL,
                    (void *volatile *) QUEUE_GET_MSGS_LOC(queue->incoming))) {
            all = QUEUE_GET_MSGS(queue->incoming);
        }
        o2_message_ptr pending = NULL;
        // list reversal: at top of loop, all has the unreversed list and
        //   pending has the reversed list. Loop body pops from all and pushes
        //   onto pending
        while (all) {
            tmp = all; // pop from all
            all = all->next;
            tmp->next = pending; // push onto pending
            pending = tmp;
        }
        queue->pending = pending;
        // we got reverse of incoming into pending
    }
    // return first message from pending list
    tmp = queue->pending;
    if (tmp) {
        queue->pending = tmp->next;
    }
    return tmp;
}


void o2x_msg_enqueue(o2x_msg_queue_ptr queue, o2_message_ptr msgptr)
{
    OSAtomicEnqueue(&queue->incoming, msgptr, 0);
}


int o2x_msg_queue_empty(o2x_msg_queue_ptr queue)
{
    return (QUEUE_GET_MSGS(queue->incoming) == NULL) && (queue->pending == NULL);
}
