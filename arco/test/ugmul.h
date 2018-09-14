void arc_op_mul_aa_a_new(o2_msg_data_ptr msg, char *types, 
                         char *data, Engine_ptr eng);

class Ug_mul_aa_a: public Ugen {
  public:
    sample_type *in1;
    sample_type *in2;
    sample_type out[ARC_BLEN];

    Ug_mul_aa_a(sample_type *in1, sample_type *in2) {
        this->in1 = in1;
        this->in2 = in2;
    }

    ~Ug_mul_aa_a() { ; }

    void run() {
        for (int i = 0; i < ARC_BLEN; i++) {
            out[i] = in1[i] * in2[i];
        }
    }

    sample_type *output(int i) {
        assert(i == 0);
        return out;
    }
};
