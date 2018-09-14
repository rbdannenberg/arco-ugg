/* engine.h -- audio engine for arco
 *
 * Roger B. Dannenberg
 * May 2018
 */

/* setting inputs and outputs of instruments:
    each input is a Ugen
    inputs keep a list of instruments that source them and
        everything on the list is summed to the input buffer
    connections are made by 
        op_set_input arg=channel, instr=instr, ugen=input_ugen
    connections are broken by
        op_break_input arg=channel, instr=instr, ugen=input_ugen
    each output is an actual ugen in some other instrument
    outputs are defined by
        op_set_output arg=outputchannel, instr=source ugen channel, ugen=source ugen
    after this operation,
        instrument's outputchannel is pointer to a block in a ugen
   
    destroying instruments:
        instrument has to have backpointers for every connection to its output. 
        When an instrument is deleted we send a op_break_input to everyone we 
          are connected to.
        instrument also uses inputs list to remove backpointers
 */

/* msg format is:
   length (32 bits)
   ignore (32 bits) -- used for lock-free queue implementation
   timestamp (64 bits)
   opcode (16 bits) -- the operation
   arg    (16 bits) -- a short argument, e.g. to name a parameter
   ugen   (32 bits) -- operand, normally 16 bits of instrument ID 
                       followed by 16 bits of UGEN index
   ...              -- additional parameters

   "templates" are just messages that build instruments. The 
   messages contain zero as the instrument number, indicating
   "current instrument". Template data is simply message data
   copied into buffers that are linked together. An extra pointer
   at the beginning serves as link to the next buffer.

   message data in templates looks like sequence of
     op-arg-ugen, params..., op-arg-ugen, params..., ...
*/


#define MAXMSGLEN 32
#define MAXINSTRUMENT 100
#define CREATING_INSTR 1
#define CREATING_TEMPLATE 2

#define ARC_INSTRUMENT(id) ((id) >> 32)
#define ARC_UGEN(id) (((id) >> 16) & 0xFFFF)
#define ARC_BLOCK(id) ((id) & 0xFFFF)

class Engine;
typedef Engine *Engine_ptr;

typedef void (*arc_method_handler)(const o2_msg_data_ptr msg,
                              char *type_string,
                              char *data, Engine_ptr eng);

class Engine {
  public:
    o2_message_ptr msg;
    o2x_msg_queue in_queue;
    o2x_msg_queue out_queue;
    Instr_ptr *instruments; // array of instruments
    int32 *build_ptr; // used to iterate through message
                      // this points to the length field
    bool have_msg;
    int state; // CREATING_INSTR, CREATING_TEMPLATE, or 0
    Instr_template_ptr templ; // currently building template
    Instr_ptr instrument;  // currently building instrument
    int error;
    node_entry msg_table;

    Engine(int qlen);
    ~Engine();

    void add_operation(const char *path, const char *types, arc_method_handler handler);
    // add a unit generator to current instrument according to msg
    void add_to_instrument(o2_msg_data_ptr msg);

    void poll(double realtime);
    void execute(o2_msg_data_ptr msg);
    void op_start();
    void op_finish();
    void op_create();
    void op_destroy();
};

void arc_op_ping(o2_msg_data_ptr msg, char *types, 
                 char *data, Engine_ptr eng);
void arc_op_ins_def(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng);
void arc_op_ins_end(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng);
void arc_op_ins_new(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng);
void arc_op_ins_del(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng);
