// mult declarations

class Mult_aa_a : public Ugen_outa {
    Ugen *a;
    Ugen *b;

  public:
    Mult_aa_a(Ugen *a, Ugen *b);
    void run(long block_num);
};

class Mult_ab_a : public Ugen_outa {
    Ugen *a;
    Ugen *b;
    sample b_arate;

  public:
    Mult_ab_a(Ugen *a, Ugen *b);
    void run(long block_num);
};

class Mult_bb_b : public Ugen_outb {
    Ugen *a;
    Ugen *b;

  public:
    Mult_bb_b(Ugen *a, Ugen *b);
    void run(long block_num);
};

