// opcodes.cpp - obsolete

#include <stddef.h>
#include <sys/types.h>
#include "arcocommon.h"
#include "opcodes.h"
#include "mem.h"
#include "message.h"
#include "instr.h"
#include "o2_internal.h"
#include "o2_search.h"
#include "engine.h"
#include "opmul.h"

#ifdef IGNORE
Arc_op arc_ops[MAX_OPCODE] = {
/* 0 */       &arc_op_start,
/* 1 */       NULL,
/* 2 */       &arc_op_create,
/* 3 */       &arc_op_destroy,
/* 4 */       &arc_op_mul_aa_a
};
#endif

