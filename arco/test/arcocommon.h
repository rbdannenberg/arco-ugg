// arcocommon.h - common includes for all arco implementation files

#include <stddef.h>
#include <sys/types.h>

typedef int64_t int64_t;
typedef int32_t int32;
typedef int16_t int16;
typedef float sample_type;

typedef int Arc_error;
#define NOERROR 0
#define BUFFEROVERFLOW -1

#include "o2.h"
#include "o2_dynamic.h"
#include "ugen.h"
