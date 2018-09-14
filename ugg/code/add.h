// add declarations

class Add_aa_a : public Ugen_outa {
    Ugen *a;
    Ugen *b;

  public:
    Add_aa_a(Ugen *a, Ugen *b);
    void run(long block_num);
};

class Add_ab_a : public Ugen_outa {
    Ugen *a;
    Ugen *b;
    sample b_arate;

  public:
    Add_ab_a(Ugen *a, Ugen *b);
    void run(long block_num);
};

class Add_bb_b : public Ugen_outb {
    Ugen *a;
    Ugen *b;

  public:
    Add_bb_b(Ugen *a, Ugen *b);
    void run(long block_num);
};

