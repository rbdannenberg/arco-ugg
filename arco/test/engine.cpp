/* engine.cpp -- audio engine for arco
 *
 * Roger B. Dannenberg
 * May 2018
 */

#include "arcocommon.h"
#include <sys/types.h>
#include "mem.h"
#include "queue.h"
// #include "message.h"
#include "instr.h"
#include "o2_internal.h"
#include "o2_search.h"
#include "engine.h"
#include "ugmul.h"

typedef struct arc_handler_entry {
    int tag; // must be PATTERN_HANDLER
    o2string key; // key is "owned" by this handler_entry struct
    o2_entry_ptr next;
    const char *type_string;
    arc_method_handler handler;
} arc_handler_entry, *arc_handler_entry_ptr;


static char synth_service_name[16];



void arc_set_synth_name(const char *name)
{
    strlcpy(synth_service_name, name, sizeof(synth_service_name));
}


void Engine::add_operation(const char *path, const char *types,
                            arc_method_handler handler)
{
    arc_handler_entry_ptr entry = (arc_handler_entry_ptr) o2x_alloc(sizeof(arc_handler_entry));
    entry->tag = PATTERN_HANDLER;
    char fullpath[64];
    strlcpy(fullpath, synth_service_name, sizeof(fullpath));
    strlcat(fullpath, path, sizeof(fullpath));
    entry->key = o2_heapify(fullpath);
    entry->next = NULL;
    entry->type_string = o2_heapify(types);
    entry->handler = handler;
    o2_entry_add(&msg_table, (o2_entry_ptr) entry);
}


Engine::Engine(int qlen)
{
    o2x_msg_queue_init(&in_queue);
    o2x_msg_queue_init(&out_queue);
    instruments = (Instr_ptr *) o2x_alloc(MAXINSTRUMENT * sizeof(Instr_ptr));
    build_ptr = NULL;
    have_msg = false;
    state = 0;
    templ = NULL;
    instrument = NULL;
    error = NOERROR;
    o2_node_initialize(&msg_table, NULL);
    arc_set_synth_name("/syn");
    add_operation("/ping", "i", &arc_op_ping);
    add_operation("/ins/def", "hB", &arc_op_ins_def);
    add_operation("/ins/end", "", &arc_op_ins_end);
    add_operation("/ins/new", "h", &arc_op_ins_new);
    add_operation("/ins/del", "h", &arc_op_ins_del);
    add_operation("/mul_aa_a/new", "ii", &arc_op_mul_aa_a_new);
}


Engine::~Engine()
{
    o2_node_finish(&msg_table);
}


void Engine::poll(double realtime)
{
    if (!have_msg) {
        msg = o2x_msg_dequeue(&in_queue);
        if (!msg) {
            return;
        }
        have_msg = true;
    }
    if (msg->data.timestamp > realtime) {
        return; // not time for message yet
    }
    // first int32 in msgbuf is length, so O2 msg starts at offset 1
    execute((o2_msg_data_ptr) &msg->data);
    msg->data.address[0] = 0; // mark message as simply a return to free
    o2x_msg_enqueue(&out_queue, msg);
    have_msg = false;
}


void Engine::execute(o2_msg_data_ptr msg)
{
    // address should be of the form /syn/<class>/<action>, where <class> is 
    // a UG name or "ins", and <action> is a UG parameter name to set or
    // an instrument action: "new" (instantiate a template if <class> is "ins",
    // or define a Ugen if <class> is a Ugen), "del" (delete an instance), 
    // "def" (define an instrument either as a template or to create a single 
    // instance)

    char *types = msg->address;
    types[0] = '/'; // force out '!' just in case
    // find the type string after the address
    while (types[3]) types += 4;
    types += 5; // start looking at types after the initial ','
    arc_handler_entry_ptr handler = (arc_handler_entry_ptr) 
            *o2_lookup(&msg_table, msg->address);
    if (handler) {
        int types_len = (int) strlen(types);
        if (!streql(handler->type_string, types)) {
            return;
        }
        // tricky pointer math: types is at offset 1 from word boundary,
        // data is next word boundary after zero end-of-string
        char *data = types + ((types_len + 1 & ~3) + 3);
        (*(handler->handler))(msg, types, data, this);
    }
}


/*

    if (!state) {
        (*(arc_ops[msg->opcode]))(this, msg);
    } else if (state == CREATING_TEMPLATE) {
        assert(building);
        templ->add(msg);
    } else if (state == CREATING_INSTR) {
        add_to_instrument(msg);
    } else {
        assert(false);
    }
}
*/


#define PADDED_LEN(i) (((i) + 4) & ~3)
#define ARC_INT64_PARAM(var) int64_t var = *((int64_t *) data); data += sizeof(int64_t);
#define ARC_INT32_PARAM(var) int32 var = *((int32 *) data); data += sizeof(int32);
#define ARC_BOOL_PARAM(var) ARC_INT32_PARAM(var)
#define ARC_STRING_PARAM(var) char *var = ((char *) data); data += PADDED_LEN(strlen(var));

void arc_send(Engine_ptr eng, o2_message_ptr msg, int msg_len, double timestamp)
{
    msg->next = NULL;
    msg->tcp_flag = 0;
    msg->allocated = msg_len;
    msg->length = msg_len;
    msg->data.timestamp = 0.0;
    o2x_msg_enqueue(&eng->out_queue, msg);
}


/* arc_op_ping - are you alive? Echo an int
 *      O2_STRING reply_to
 *      O2_INT32 value
 */
void arc_op_ping(o2_msg_data_ptr msg, char *types,
                 char *data, Engine_ptr eng)
{
    ARC_STRING_PARAM(addr);
    ARC_INT32_PARAM(val);
    // build outgoing message
    int64_t addr_len = PADDED_LEN(strlen(addr) + 10); // add room for /get-reply and pad
    int msg_len = (int) MESSAGE_SIZE_FROM_ALLOCATED(sizeof(double) + addr_len + 4 + sizeof(int32_t));
    o2_message_ptr m = (o2_message_ptr) o2x_alloc(msg_len);
    char *dst = m->data.address;
    char *last = dst + addr_len;
    size_t ilast = PADDED_LEN((size_t) last);
    *((int32_t *) (ilast - 4)) = 0;
    memcpy(dst, addr, addr_len);
    memcpy((char *) ilast, ",i\0", 4); // type string
    *((int32_t *) (ilast + 4)) = val;
    arc_send(eng, m, msg_len, 0.0);
}


/* arc_op_ins_def - begin the creation of an instrument.
 *     O2_INT64 id
 *     O2_BOOL  instantiate
 */
void arc_op_ins_def(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng)
{
    // types have already been checked
    ARC_INT64_PARAM(id);
    ARC_BOOL_PARAM(instantiate_flag);
    eng->state = (instantiate_flag ? CREATING_INSTR : CREATING_TEMPLATE);
    if (eng->state == CREATING_TEMPLATE) { // copy rest of message to template object
        eng->templ = new Instr_template();
        eng->instruments[ARC_INSTRUMENT(id)] = (Instr *) eng->templ;
    } else { // CREATING_INSTR
        eng->instrument = new Instr();
        eng->instruments[ARC_INSTRUMENT(id)] = eng->instrument;
    }
}


void arc_op_ins_end(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng)
{
    eng->state = 0;
}


/* arc_op_ins_new - instantiate an instrument from a template.
 *     O2_INT64 id -- instrument field is the template, 
 *                    ugen field is the new instance
 */
void arc_op_ins_new(o2_msg_data_ptr msg, char *types, 
                    char *data, Engine_ptr eng)
{
    ARC_INT64_PARAM(id);
    int inst = ARC_UGEN(id);
    id = ARC_INSTRUMENT(id);
    
    // find and instantiate template
    eng->instruments[inst] = ((Instr_template_ptr) eng->instruments[id])->instantiate(eng);
}


/* arc_op_ins_del - delete an instrument
 *     O2_INT64 id -- what to delete
 */
void arc_op_ins_del(o2_msg_data_ptr msg, char *types,
                    char *data, Engine_ptr eng)
{
    ARC_INT64_PARAM(id);
    id = ARC_INSTRUMENT(id);
    // find instrument
    delete eng->instruments[id];
    eng->instruments[id] = NULL;
}


/* arc_op_mul_aa_a_new - add a mul_aa_a ugen
 *     O2_INT32 input 1
 *     O2_INT32 input 2
 */
void arc_op_mul_aa_a_new(o2_msg_data_ptr msg, char *types,
                         char *data, Engine_ptr eng)
{
    if (eng->state == CREATING_TEMPLATE) {
        eng->templ->add(msg, types, data, eng);
    } else { // CREATING_INSTR
        Instr_ptr ins = eng->instrument;
        ARC_INT32_PARAM(inp1);
        sample_type *buf1 = ins->ugens[ARC_UGEN(inp1)]->output(ARC_BLOCK(inp1));
        ARC_INT32_PARAM(inp2);
        sample_type *buf2 = ins->ugens[ARC_UGEN(inp2)]->output(ARC_BLOCK(inp2));
        
        Ugen_ptr ugen = new Ug_mul_aa_a(buf1, buf2);
        ins->ugens.append(ugen);
    }
}


