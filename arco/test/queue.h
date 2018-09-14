/* queue.h -- some helpful utilities for building midi 
               applications that use PortMidi 

   A queue based on lock-free list primitives.
   The queue holds O2 messages (o2_message)
   To receive messages, we unlink the incoming list, reverse the list, and
   dispatch the messages.
 */

#ifdef __cplusplus
extern "C" {
#endif

#include <libkern/OSAtomic.h>

#ifdef __APPLE__
#define o2x_queue_head OSQueueHead
#define QUEUE_INIT(q) (q).opaque1 = 0; (q).opaque2 = 0;
#define QUEUE_GET_MSGS(q) ((o2_message_ptr) (q).opaque1)
#define QUEUE_GET_MSGS_LOC(q) (&(q).opaque1)
#else
#error non-apple implementation needed
#endif

typedef struct {
    o2x_queue_head incoming; // messages are inserted here
    o2_message_ptr pending;  // messages in correct order are here
} o2x_msg_queue, *o2x_msg_queue_ptr;

void o2x_msg_queue_init(o2x_msg_queue_ptr queue);

o2_message_ptr o2x_msg_dequeue(o2x_msg_queue_ptr queue);

void o2x_msg_enqueue(o2x_msg_queue_ptr queue, o2_message_ptr msgptr);

int o2x_msg_queue_empty(o2x_msg_queue_ptr queue);

#ifdef __cplusplus
}
#endif
