// instr.h - instr subclass of ugen, also (instrument) Templates
//
// Roger B. Dannenberg
// Mar 2018

/* design notes:
An Instr is a collection of Ugens referenced by an array of pointers that
also gives the order of execution.

The Instr is the unit of dynamic patching. An Instr has N inputs and M
outputs. You can "plug" or "unplug" an Instr output from an Instr input
at runtime. The connections are one to many and many to one. Fan-in 
(many-to-one) means the inputs are summed, and zero inputs means the
input is zero.

An Instr is not connected to anything upon creation. An Instr may be
destroyed, in which case its outputs are automatically unplugged and
any Instr's that are plugged into the destroyed Instr are unplugged
as well.

Connection go to Ugens of subclass Input. An Input has a list of pointers
to blocks that are summed by the Input Ugen. Each pointer must also carry
the ID of the Instr so that when the Instr is destroyed we can remove the
right pointer. To "plug in", we send a op_plugin message containing: The
ID of the Instr serving as the source, the ID of the Ugen serving as the 
source, the output number of the Ugen, the ID of the Instr we are plugging
into, the ID of the Input we are plugging into. This allows us to resolve the 
address of a source sample block. The address and the source Instr ID are
linked onto the target Input.

On the other side, an Instr that is plugged into another Instr needs to be
able to resolve the Input Ugen so that it can be unplugged when the source
Instr is destroyed. The Input is identified by the Instr ID and Input ID.
These can be linked onto the Instr itself rather than the connected Ugen.

When an Instr is destroyed we need to disconnect "upstream" and "downstream".
To disconnect "upstream", go to each Input (Inputs are the first N in the
Ugens array). Follow the linked list of connections. For each connection, 
get the Instr, go to the Instr, and remove the link with the matching Instr
ID and Input ID.

To disconnect "downstream", repeatedly take the first thing on the list, and 
"unplug" using the Instr ID and Input ID. The unplug operation will come back
to this Instr and search the list to remove the connection, but it will be
the first connection on the list.

Summary of list nodes:
For Input Ugens:
    next
    sample (block) pointer
    Instr ID, Ugen ID
For Instr:
    next
    Instr ID, Ugen ID

For simplicity, let's just use one list node type for both; in fact, let's
use the pointer to go directly to the Input Ugen.
*/


class Engine;
typedef Engine *Engine_ptr;

class Input;
typedef Input *Input_ptr;

typedef class Connection {
  public:
    Connection *next;
    union {
        sample_type *src; // for connection list on Input sink
        Input_ptr input;  // for connection list on Instr source
    } ptr;
    int32 id;

    void *operator new(size_t size);
    void operator delete(void *ptr);
} *Connection_ptr;


typedef class Instr : public Ugen {
  public:
    int next;
    Engine_ptr engine;
    Ugen_array ugens;
    Connection_ptr sinks;
    Ugen_array inputs;
    Int32_array outputs;
    int ninputs;
    int noutputs;

    Instr();
    ~Instr();

    void run();
    void unplug(int32 id, Engine_ptr engine);
    sample_type *output(int i);
    void add(o2_msg_data_ptr msg);
    Ugen_ptr lookup(int32 id) { return ugens[id]; }
} *Instr_ptr;


typedef class Instr_template : public Instr {
  public:
    o2_message_ptr msgs;
    o2_message_ptr last;
    Instr_template() { msgs = last = NULL; }
    ~Instr_template();
    Instr_ptr instantiate(Engine_ptr eng);
    void add(o2_message_ptr msg, char *types,
             char *data, Engine_ptr eng);
} *Instr_template_ptr;

typedef class Input : public Ugen {
  public:
    Connection_ptr sources;

    void unplug(int32 id, Engine_ptr eng);
} *Input_ptr;

typedef class Input_a : public Input {
  public:
    sample_type block[ARC_BLEN];
} *Input_a_ptr;

typedef class Input_b : public Input {
  public:
    sample_type sample;
} *Input_b_ptr;

