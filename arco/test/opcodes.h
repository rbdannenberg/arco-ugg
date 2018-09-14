// opcodes.h

class Engine;
typedef Engine *Engine_ptr;

class Message;
typedef Message *Message_ptr;

#define MAX_OPCODE 100
typedef void (*Arc_op)(Engine_ptr eng, Message_ptr msg);

extern int num_opcodes;
extern Arc_op arc_ops[MAX_OPCODE];
