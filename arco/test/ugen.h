// ugen.h - superclass
//
// Roger B. Dannenberg
// Mar 2018

#define ARC_BLEN 32

typedef class Ugen {
  public:
    virtual ~Ugen() { ; };
    virtual void run() { ; }
    virtual sample_type *output(int i) { return NULL; }
    void *operator new(size_t size);
    void operator delete(void *ptr);
} *Ugen_ptr;


class Ugen_array {
  protected:
    dyn_array array;
  public:
    Ugen_array() { DA_INIT(array, Ugen_ptr, 4); }
    ~Ugen_array() { DA_FINISH(array); }
    Ugen_ptr &operator[](int i) { return *DA_GET(array, Ugen_ptr, i); }
    int length() { return array.length; }
    void append(Ugen_ptr ug) { DA_APPEND(array, Ugen_ptr, ug); }
    void destroy();
};


class Int32_array {
  protected:
    dyn_array array;
  public:
    Int32_array() { DA_INIT(array, int32, 4); }
    ~Int32_array() { DA_FINISH(array); }
    int32 &operator[](int i) { return *DA_GET(array, int32, i); }
    void append(int32 an_int) { DA_APPEND(array, int32, an_int); }
    // void destroy(); nothing to destroy
};
