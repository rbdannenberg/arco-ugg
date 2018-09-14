// message.h - message declaration
//
// Roger B. Dannenberg
// Mar 2018

/*
O2 message data:
length (at negative offset)
timestamp
address
typestring
int64_t instrument/ugen/channel
more parameters

we will store sequences of messages by stripping off timestamps, 
but using int32 lengths for each message. We will pass them off
as o2_msg_data_ptr, where the pointer is actually 4 bytes before
the length where the timestamp should be.


typedef struct Message {
    int32 length;
    int32 ignore;
    double timestamp;
    int16 opcode;
    int16 arg;
    int16 instrument;
    int16 ugen;
    char parameters[8]; // may be of any length
} *Message_ptr;


*/
