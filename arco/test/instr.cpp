// instr.cpp - instrument subclass of ugen
//
// Roger B. Dannenberg
// Mar 2018

#include "arcocommon.h"
#include <string.h>
#include "message.h"
#include "mem.h"
#include "instr.h"
#include "o2_internal.h"
#include "o2_search.h"
#include "queue.h"
#include "engine.h"
#include <iostream>

using namespace std;

void *Connection::operator new(size_t size)
{
    return o2x_alloc(size);
}

void Connection::operator delete(void *ptr)
{
    o2x_free(ptr);
}



Instr::Instr()
{
    next = 0;
}


Instr::~Instr()
{
    // unplug all inputs
    for (int i = 0; i < inputs.length(); i++) {
        Input_ptr inp = (Input_ptr) inputs[i];
        while (inp->sources) {
            inp->unplug(inp->sources->id, engine);
        }
    }
    // unplug all outputs
    while (sinks) {
        sinks->ptr.input->unplug(sinks->id, engine);
    }
    // inputs/outputs will be freed by ~Ugen_array.
    // do not call inputs.destroy() because all Inputs are
    // also in ugens and are deleted by the next call...
    // free all ugens
    ugens.destroy();
}


void Instr::run()
{
    return;
}


// should only be called by Input::unplug. Used to remove connection
// from instrument to a sink
void Instr::unplug(int32 sink, Engine_ptr engine) 
{
    for (Connection_ptr *cptr = &sinks; *cptr; cptr = &((*cptr)->next)) {
        if ((*cptr)->id == sink) {
            Connection_ptr con = *cptr; // unlink
            *cptr = (*cptr)->next;
            o2x_free(con); // delete
            return;
        }
    }
}


sample_type *Instr::output(int i)
{
    int32 ug_out = outputs[i];
    Ugen_ptr ug = ugens[ARC_UGEN(ug_out)];
    return ug->output(ARC_BLOCK(ug_out));
}


void Instr_template::add(o2_message_ptr msg, Engine_ptr eng)
{
    if (!last) {
        msgs = msg;
    } else {
        last->next = msg;
    }
    last = msg;
    last->next = NULL;
}


Instr_ptr Instr_template::instantiate(Engine_ptr eng)
{
    Instr_ptr inst  = new Instr();
    o2_message_ptr msg = msgs;
    while (msg) {
        eng->execute(&(msg->data));
        msg = msg->next;
    }
    return inst;
}


Instr_template::~Instr_template()
{
    while (msgs) {
        o2_message_ptr first = msgs;
        msgs = msgs->next;
        o2x_free(first);
    }
    last = NULL;
}


void Input::unplug(int32 id, Engine_ptr engine)
{
    // find id in sources
    for (Connection_ptr *cptr = &sources; *cptr; cptr = &((*cptr)->next)) {
        if ((*cptr)->id == id) {
            Connection_ptr con = *cptr; // unlink
            *cptr = (*cptr)->next;
            // find instrument and remove connection
            Instr_ptr instr = engine->instruments[ARC_UGEN(id)];
            instr->unplug(id, engine);
            o2x_free(con); // delete
            return;
        }
    }
    cout << "Warning: Input::unplug did not find " << id << std::endl;
}
