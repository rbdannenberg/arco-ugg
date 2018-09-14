// osci declarations

class Osci_acc_a : public Ugen_outa {
    Table_ptr table;
    double phase;
    int table_len;
    Ugen *hz;
    double indexf;

  public:
    Osci_acc_a(Ugen *hz, double phase, Table_ptr table);
    void run(long block_num);
};

class Osci_bcc_a : public Ugen_outa {
    Table_ptr table;
    double phase;
    int table_len;
    Ugen *hz;
    double indexf;

  public:
    Osci_bcc_a(Ugen *hz, double phase, Table_ptr table);
    void run(long block_num);
};

class Osci_ccc_a : public Ugen_outa {
    Table_ptr table;
    double phase;
    int table_len;
    double hz;
    sample t2;
    double indexf;

  public:
    Osci_ccc_a(double hz, double phase, Table_ptr table);
    void run(long block_num);
};

