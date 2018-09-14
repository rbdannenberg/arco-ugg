/* queue.c -- non-blocking queue
 */
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include "mem.h"
#include "queue.h"

#ifdef WIN32
#define bzero(addr, siz) memset(addr, 0, siz)
#endif

void o2_msg_queue_init(o2x_msg_queue_ptr queue)
{
    QUEUE_INIT(queue->incoming);
    queue->pending = NULL;
}


o2_message_ptr o2_msg_dequeue(o2_msg_queue_ptr queue)
{
    o2_msg_queue_ptr result = NULL;
    if (!queue->pending) {
        o2_message_ptr all = QUEUE_GET_MSGS(queue->incoming);
        if (!all) {
           return result;
        }
        // store zero if nothing has changed
        while (!OSAtomicCompareAndSwapPtrBarrier(all, NULL,
                        &QUEUE_GET_MSGS(queue->incoming)) {
            all = QUEUE_GET_MSGS(queue->incoming);
        }
        o2_message_ptr next = NULL;
        while (all) {
            next = all->next;
            all->next = result;
            result = all;
            all = next;
        }
        // we got reverse of incoming into result
    }
    // return first message from pending list
    queue->pending = result->next;
    return result;
}


void o2_msg_enqueue(o2_msg_queue_ptr queue, o2_message_ptr msgptr)
{
    OSAtomicEnqueue(&queue->incoming
}


int o2_msg_queue_empty(o2_msg_queue_ptr queue)
{
    return (queue->pending == NULL) && (queue->incoming == NULL);
}
