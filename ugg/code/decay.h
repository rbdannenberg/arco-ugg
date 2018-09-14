// decay declarations

class Decay_cc_a : public Ugen_outa {
    sample amp;
    sample time;
    sample dursamples;
    sample decay;
    sample state;

  public:
    Decay_cc_a(sample amp, sample time);
    void run(long block_num);
    void set_amp(sample amp);
};

