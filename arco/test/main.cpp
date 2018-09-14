//
//  main.cpp
//  arco
//
//  Created by Roger Dannenberg on 3/25/18.
//  Copyright © 2018 Roger Dannenberg. All rights reserved.
//

#include <iostream>
#include "arco.h"
#include "porttime.h"

void synth_callback(PtTimestamp timestamp, void *data)
{
    Engine_ptr eng = (Engine_ptr) data;
    eng->poll(o2_time_get());
}


void send_test_message(Engine &eng)
{
    o2_send_start();
    o2_add_int64(10);
    o2_add_bool(true);
    o2_message_ptr m = o2_message_finish(0.0, "/syn/ins/def", 1);
    o2x_msg_enqueue(&eng.in_queue, m);
}


int main(int argc, const char * argv[])
{
    o2_initialize("test");
    std::cout << "Hello, World!\n";
    o2x_mem_init(NULL, 0, true);
    Engine eng(256);
    Pt_Start(1, synth_callback, &eng);

    // send a test message
    send_test_message(eng);

    // test: call o2 and arco polling functions
    o2_initialize("arco");
    o2_clock_set(NULL, NULL);
    while (true) {
        o2_poll();
        usleep(1000);
    }
    return 0;
}
