// ugen.h -- base for unit generators

#include "stdlib.h"
#include "math.h"

#define AR 44100.0
#define AR_RECIP (1.0 / AR)
#define BL 32
#define BR (AR / BL)
#define BR_RECIP (BL / AR)

typedef float sample;

typedef struct {
    int len; // actual number of samples in data
    sample data[2];
} Table, *Table_ptr;


extern Table_ptr SINETABLE;

extern long ugg_block_count;


// create table of length len, not including the extra
// sample at the end
Table *table_create(int len);
#define tblget(table, index) ((table)->data[index])
#define tblput(table, index, value) ((table)->data[index] = (value))
// table is stored with redundant last element to facilitate
// interpolation, so effective len is actual len - 1:
#define table_len(table) ((table)->len - 1)

inline double phase_wrap(double phase, int len)
{
    double p = phase;
    double n = len;
    while (p > n) p -= n;
    return p;
}

//#define phase_wrap fmod


class Ugen {
  public:
    Ugen();
    long block_count;
    virtual sample *get_outs() = 0;
    virtual sample get_out() = 0;
    virtual void run(long block_num) = 0;
};

typedef Ugen *Ugen_ptr;

class Ugen_outa : public Ugen {
  public:
    Ugen_outa();
    virtual sample *get_outs();
    virtual sample get_out();
    sample outs[BL];
};

class Ugen_outb : public Ugen {
  public:
    Ugen_outb();
    virtual sample *get_outs();
    virtual sample get_out();
    sample out;
};


double uniform();
