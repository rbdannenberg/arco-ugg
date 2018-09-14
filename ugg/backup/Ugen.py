# Ugen - functional style unit generator system
#
# Roger B. Dannenberg

# General Ugen form:
#
# class Name : Ugen_out[r] {
#     <gen_declarations>
#
#     void Name(parameters) {
#          block_count = 0;
#          <gen_constructor>
#     }
#
#     void run(long block_num) {
#         <gen_update_inputs> // topological sort
#         block_count = block_num;
#         <gen_brate_code() side effect output>
#         <gen_brate_code>
#         <gen_upsample_prep>
#         ****** for loop only if out rate is AR *****
#         for (int i = 0; i < BL; i++) {
#             <gen_arate_code>
#             out[i] = <out.gen_code()>;
#             <gen_next_arate_state>
#             <gen_upsample_update>  // BR upsampling updates 
#             <update_arate_state>  // AR state = state_next
#         }
#         ****** this form only if out rate is BR *****
#         <out.gen_code() side-effect-output>
#         out = <out.gen_code()>;
#         ****** end of BR form ******
#
#     }

# topological sort implementation of <gen_update_inputs>:
# for each Param:
#     if Param rate is < CR:
#         generate this: 
#             if (param->block_count < block_num)
#                 param->run(block_num);
# declarations include 
UGG_INDENT = 2
UGG_STATE = "ugg_state"

def error(*args):
    print("\n**** ERROR: ", end="")
    for arg in args:
        print(str(arg), sep=" ", end="")
    print(" ****")
    get_a_stack_trace()


class Ugen:
    def __init__(self, value=None):
        if value != None:
            self.op = "const"
            self.value = value
        self.parameters = []
        self.visited = False
        self.upsample = False
        self.interpolate_ok = True
        self.output_rate = False
        self.rate = None
        self.name = None

    def copy(self):
        new = Ugen(self.value)
        self.copy_fields_to(new)
        return new

    def copy_fields_to(self, dest):
        dest.parameters = self.parameters.copy()
        dest.visited = self.visited
        dest.upsample = self.upsample
        dest.interpolate_ok = self.interpolate_ok
        dest.output_rate = self.output_rate
        dest.rate = self.rate
        dest.name = self.name
        return dest

    def update_refs(self, m):
        # m maps old to new, parameters is already a copy
        p = self.parameters
        for i in range(len(p)):
            # replace each parameter with a mapped version. If the mapping
            #    is already done for some reason, default to existing value
            p[i] = m.get(p[i], p[i])

    def __str__(self):
        return "<Ugen " + str(self.value) + ">"

    def __add__(self, right):
        return UAdd(self, right)

    def __sub__(self, right):
        return USubtract(self, right)

    def __mul__(self, right):
        return UMul(self, right)

    def __truediv__(self, right):
        return UDiv(self, right)

    def __getitem__(self, key):
        return USubscript(self, key)

    def print_tree(self):
        global to_be_printed
        global printed
#        print("adding", self, "to to_be_printed")
        to_be_printed = [self]
        printed = []
        while len(to_be_printed) > 0:
            to_print = to_be_printed[-1]
            printed.append(to_print)
            to_print.print_subtree(0)
            to_be_printed.remove(to_print)

    def print_self(self, depth, text):
        up = str(self.upsample) if self.upsample else ""
        print(" " * depth * UGG_INDENT, text, " ", self.rate, "r ", up, sep="")

    def print_subtree(self, depth):
        self.print_self(depth, "const " + str(self.value))

    def gen_code(self):
        return str(self.value)

    def get_ugen_list(self):
#        print("ENTER get_ugen_list of: " + str(self))
        ugens = self.get_ugen_list2(1)
        for ugen in ugens:
            ugen.visited = False
        return ugens

    # when we recursively find all ugens, we need to get the things 
    # this Ugen depends upon. Normally, this is everything in 
    # parameters, which is created by all Ugen subclasses for 
    # convenience, but in one case, class State, the ugen also 
    # depends upon next (a State has two dependencies: the initial 
    # value created by First(), which puts the expression in parameters,
    # and every successive value, as indicated by Next(), which puts the
    # expression in rest.
    def get_all_parameters(self):
        return self.parameters

    # recursive helper function
    def get_ugen_list2(self, depth):
        ugens = [self]
#        print_ugens(str(depth) + " enter get_ugen_list2 for", ugens)
#        if self.upsample:
#            ugens.append(self.upsample)
        self.visited = True
        for ugen in self.get_all_parameters():
#            print(depth, "in self.parameters:", str(ugen), type(ugen), end=" ")
#            print(str(ugen.visited))
            if not ugen.visited:
                new_ugens = ugen.get_ugen_list2(depth + 1)
#                print_ugens(str(depth) + " Adding new ugens:", new_ugens)
                ugens = ugens + new_ugens
#                print_ugens(str(depth) + " To get", ugens)
#        print_ugens(str(depth) +  " before reverse", ugens)
        ugens.reverse()
#        print_ugens(str(depth) + " RETURN:", ugens)
        return ugens

    def use_output_rate(self):
        self.output_rate = True

    def use_non_interpolated(self):
        self.interpolate_ok = False

    def find_rate(self, out_rate):
        if self.output_rate:
            self.rate = out_rate
        if not self.rate:
            self.rate = CR
            for ugen in self.parameters:
                if ugen.find_rate(out_rate) < self.rate:
                    self.rate = ugen.rate  # go as fast as any we depend on
        if self.rate == CR and isinstance(self, First):
            self.rate = BR  # state variable is at least block rate
        return self.rate

    def gen_declarations(self):
        return None

    def gen_update_input(self):
        return None

    def gen_arate_code(self):
        return None

    def gen_brate_code(self):
        return None

    def gen_upsample_prep(self):
        return None

    def gen_constructor(self):
        return None

    def gen_upsample_update(self):
        return None

    def gen_next_arate_state(self):
        return None

    def gen_next_state_br(self):
        return None

    def update_arate_state(self):
        return None

    def update_state_br(self):
        return None


# given a Ugen, constant, or string, produce a Ugen
#     strings denote a variable: look it up in ugg_vars
#     constants are converted to Ugen(constant)
def coerce_to_ugen(value, op):
    orig = value
    if type(value) == int or type(value) == float:
        value = Ugen(value)
        print("coerce_to_ugen value", orig, "becomes", str(value))
    elif type(value) == str:
        value = ugg_vars[value]
    if not isinstance(value, Ugen):
        error("types not compatible with ", op)
    return value


class UBinary (Ugen):
    def __init__(self, op, left, right):
        global ugg_vars
        super().__init__()
        self.op = op
        right = coerce_to_ugen(right, op)
        self.parameters.append(left)
#        print("in UBinary.__init__, right type is", type(right))
        if type(right) == str:
            error("bad right value for UBinary " + op)
        self.parameters.append(right)

    def copy(self):
        return self.copy_fields_to(UBinary(self.op, self.parameters[0],
                                           self.parameters[1]))

    def copy_fields_to(self, dest):
        dest.op = self.op
        return super().copy_fields_to(dest)

    def __str__(self):
        return "<" + self.op + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "op" + self.op)
        depth += 1

        if isinstance(self.parameters[0], Ugen):
            self.parameters[0].print_subtree(depth)
        else:
            print("SURPRISE! left operand is not a Ugen")
            print(" " * depth * UGG_INDENT, self.parameters[0])

        if isinstance(self.parameters[1], Ugen):
            self.parameters[1].print_subtree(depth)
        else:
            print("SURPRISE! right operand is not a Ugen")
            print(" " * depth * UGG_INDENT, self.parameters[1])

    def gen_code(self):
        return "(" + self.parameters[0].gen_code() + " " + self.op + " " + \
               self.parameters[1].gen_code() + ")"


class UUnary (Ugen):
    def __init__(self, op, param):
        global ugg_vars
        super().__init__()
        self.op = op
        self.parameters.append(coerce_to_ugen(param, op))

    def copy(self):
        return self.copy_fields_to(UUnary(self.op, self.parameters[0]))

    def __str__(self):
        return "<" + self.op + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "unary " + self.op)
        depth += 1

        param = self.parameters[0]
        if isinstance(param, Ugen):
            param.print_subtree(depth)
        else:
            print("SURPRISE! the operand is not a Ugen")
            print(" " * depth * UGG_INDENT, param)

    def gen_code(self):
        return self.op + "(" + self.parameters[0].gen_code() + ")"


class Ufn2 (Ugen):
    def __init__(self, op, p1, p2):
        global ugg_vars
        super().__init__()
        self.op = op
        self.parameters.append(coerce_to_ugen(p1, op))
        self.parameters.append(coerce_to_ugen(p2, op))

    def copy(self):
        return self.copy_fields_to(Ufn2(self.op, self.parameters[0], 
                                        self.parameters[1]))

    def __str__(self):
        return "<" + self.op + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "function " + self.op)
        depth += 1

        param = self.parameters[0]
        if isinstance(param, Ugen):
            param.print_subtree(depth)
        else:
            print("SURPRISE! the operand is not a Ugen")
            print(" " * depth * UGG_INDENT, param)

        param = self.parameters[1]
        if isinstance(param, Ugen):
            param.print_subtree(depth)
        else:
            print("SURPRISE! the operand is not a Ugen")
            print(" " * depth * UGG_INDENT, param)

    def gen_code(self):
        return self.op + "(" + self.parameters[0].gen_code() + ", " + \
               self.parameters[1].gen_code() + ")"


class USubscript (Ugen):
    def __init__(self, table, index):
        global ugg_vars
        super().__init__()
        self.table = table
        if type(index) == int or type(index) == float:
            index = Ugen(index)
        elif type(index) == str:
            index = ugg_vars[index]
        elif not isinstance(index, Ugen):
            error("types not compatible with " + op)
        self.index = index
        self.parameters.append(table)
        self.parameters.append(index)

    def copy(self):
        new = USubscript(self.table, self.index)
        return self.copy_fields_to(new)

    def __str__(self):
        return "<Subscript " + str(self.table) + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "subscript")
        depth += 1

        if isinstance(self.table, Ugen):
            self.table.print_subtree(depth)
        else:
            print(" " * depth * UGG_INDENT, self.table)

        if isinstance(self.index, Ugen):
            self.index.print_subtree(depth)
        else:
            print(" " * depth * UGG_INDENT, self.index)

    def gen_code(self):
        return "(" + self.table.gen_code() + ")[" +  self.index.gen_code() + "]"


class UAdd (UBinary):
    def __init__(self, left, right):
        super().__init__("+", left, right)


class USubtract (UBinary):
    def __init__(self, left, right):
        super().__init__("-", left, right)


class UMul (UBinary):
    def __init__(self, left, right):
        super().__init__("*", left, right)

class UDiv (UBinary):
    def __init__(self, left, right):
        super().__init__("/", left, right)


class Uint (UUnary):
    def __init__(self, param):
        super().__init__("int", param)

class Ufmodf (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmodf", p1, p2)

class Ufmod (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmod", p1, p2)

class Param (Ugen):
    def __init__(self, name):
        super().__init__()
        self.op = "param"
        self.name = name
        self.rate = CR

    def copy(self):
        return self.copy_fields_to(Param(self.name))

    def __str__(self):
        return "<Param " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "parameter " + self.name)

    def gen_code(self):
        if self.rate == AR:
            return self.name + "_samps[i]"
        elif self.rate == BR:
            return self.name + "->get_out()"
        else:
            return self.name

    def gen_declarations(self):
        print("    ", RATE_TO_TYPE[self.rate], " ", self.name, ";", sep="")

    def gen_update_input(self):
        if self.rate == CR:
            return
        print("        if (", self.name, "->block_count < block_num) {", sep="")
        print("            ", self.name, "->run(block_num);", sep="")
        print("        }")

    def gen_brate_code(self):
        if self.rate == AR:
            print("        float *", self.name, "_samps = ",
                  self.name, "->get_outs();", sep="")

    def gen_constructor(self):
        print("        this->", self.name, " = ", self.name, ";", sep="")


class Var (Ugen):
    def __init__(self, name, value):
        global ugg_vars
        super().__init__()
        self.op = "var"
        self.name = name
        self.parameters = [coerce_to_ugen(value, "Var initialization")]
#        print("in Var, parameter type is", type(self.parameters[0]))
        ugg_vars[name] = self

    def copy(self):
        return self.copy_fields_to(Var(self.name, self.parameters[0]))

    def __str__(self):
        return "<Var " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "var " + self.name)
        if depth == 0:
            self.parameters[0].print_subtree(depth + 1)
        elif self not in to_be_printed and self not in printed:
            to_be_printed.append(self)

    def gen_declarations(self):
        if self.rate == CR:
            print("    float ", self.name, ";", sep="")

    def gen_constructor(self):
        if self.rate == CR:
            print("        ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="")

    def gen_brate_code(self):
        if self.rate == BR:
            print("        float ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="")

    def gen_arate_code(self):
        if self.rate == AR:
            print("            float ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="")

    def gen_code(self):
        return self.name


class First (Var):
    def __init__(self, name, value, *typespec):
        super().__init__(name, value)
        if len(typespec) < 1:
            typespec = ["float"]
        self.typespec = typespec[0]
        self.rest = None

    def copy(self):
        new = self.copy_fields_to(First(self.name, self.parameters[0]))
        new.rest = self.rest
        new.typespec = self.typespec
        return new

    def update_refs(self, old_to_new):
        super().update_refs(old_to_new)
        self.rest = old_to_new[self.rest]

    def __str__(self):
        return "<State " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "state " + self.name + " " + self.typespec)
        if depth == 0:
            self.parameters[0].print_subtree(1)
            self.rest.print_subtree(1)
        elif self not in to_be_printed and self not in printed:
#            print("adding", self, "to to_be_printed")
            to_be_printed.append(self)

    # This overrides get_all_parameters() in Ugen -- this is a special case because
    # First is specified by both First() and Next(), indicating initialization and
    # each successive value, computed at audio or block rate
    def get_all_parameters(self):
        if not self.rest:
            error("State was created with First, but Next was not called",
                  "to finish the definition")
        return self.parameters + [self.rest]

    def gen_declarations(self):
        print("    ", self.typespec, " ", self.name, ";", sep="")

    def gen_constructor(self):
        print("        ", self.name, " = ",
              self.parameters[0].gen_code(), ";", sep="")

    def gen_brate_code(self):  # overrides Var.gen_brate_code
        return

    def gen_arate_code(self):  # overrides Var.gen_arate_code
        return

    def gen_next_arate_state(self):
        if self.rate != AR:
            return None
        print("            ", self.typespec, " ", self.name, "_next = ", 
              self.rest.gen_code(), ";", sep="")

    def gen_next_state_br(self):
        if self.rate != BR:
            return None
        print("        ", self.typespec, " ", self.name, "_next = ",
              self.rest.gen_code(), ";", sep="")

    def update_arate_state(self):
        if self.rate != AR:
            return None
        print("            ", self.name, " = ", self.name, "_next;", sep="")

    def update_state_br(self):
        if self.rate != BR:
            return None
        print("        ", self.name, " = ", self.name, "_next;", sep="")


def Next(var, defn):
    global ugg_vars
    if type(var) == str:
        var = ugg_vars[var]
    if not isinstance(var, First):
        error(str(var) + " in Next should be an instance of First.")
    var.rest = defn


tempnum = 0

def make_temp_name():
    global tempnum
    tempnum += 1
    return "t" + str(tempnum)


class Upsample (UUnary):
    def __init__(self, what):
        super().__init__("upsamp", what)
        self.name = make_temp_name()
        self.rate = AR

    def copy(self):
        return self.copy_fields_to(Upsample(self.parameters[0]))

    def __str__(self):
        return "<Upsample " + self.name + ">"

    def gen_upsample_prep(self):
        print("        float ", self.name, "_step = (", 
              self.parameters[0].gen_code(), " - ", self.gen_code(), 
              ") * BL_RECIP;", sep="")

    def gen_code(self):
        return self.name + "_arate"

    def gen_declarations(self):
        print("    float ", self.name, "_arate;", sep="")

    def gen_constructor(self):
        print("        ", self.name, "_arate = 0;", sep="")

    def gen_upsample_update(self):
        print("            ", self.name, "_arate += ", self.name, "_step;",
              sep="")

# ---------


RATE_TO_TYPE = {'a': "Ugen *", 'b': "Ugen *", 'c': "float "}


def ugg_begin(name):
    global ugg_name, ugg_vars, SR, variations
    ugg_name = name
    ugg_vars = {}  # mapping from strings to Var objects
    SR = Ugen("SR")
    variations = {}


def print_ugens(heading, ugens):
    print(heading, end=": [")
    for ugen in ugens:
        print(ugen, end=" ")
    print("]")


# copy the ugen graph. References must all be mapped from current
# set to new set.
# Algorithm:
#    make a shallow copy of each Ugen in ugens
#        (requires a copy method for each Ugen class)
#    make a dictionary mapping old ugens to new ugens
#    for each new ugen, map each parameter to new ugen
#
def copy_ugens(ugens, out):
    new = [x.copy() for x in ugens]
    old_to_new = {}
    for i in range(len(ugens)):
        old_to_new[ugens[i]] = new[i]
    for ugen in new:
        ugen.update_refs(old_to_new)
    return new, old_to_new[out]


def ugg_write(rates, params, out, rate):
    global ugg_name, variations

    name = ugg_name
    if len(params) > 0:
        name += "_"
    for i in range(len(params)):
        name += rates[i]
        params[i].rate = rates[i]

    # make topological sort of calculation tree
    ugens = out.get_ugen_list()
    # find ugens to upsample
    for ugen in ugens:
        if not isinstance(ugen, Param):
            ugen.rate = None
        ugen.upsample = False
    for ugen in ugens:
        ugen.find_rate(rate)
    # find ugens that need to be upsampled
    ugens, out = copy_ugens(ugens, out)  # also sets ugg_map

    for ugen in ugens:
        for i in range(len(ugen.parameters)):
            parm = ugen.parameters[i]
            if parm.rate == BR and ugen.rate == AR:
                print("need upsample for", str(parm))
                if parm.interpolate_ok:
                    if not parm.upsample:
                        parm.upsample = Upsample(parm)
                        if not parm.name:
                            parm.name = make_temp_name()
                        parm.upsample.name = parm.name
                        print("created upsample for", str(parm))
                    ugen.parameters[i] = parm.upsample
                    print("replaced parameter", i, "in", str(ugen), "with",
                          str(parm.upsample))
                elif not isinstance(parm, Var):
                    # capture computation in a var at brate, access at arate
                    if not parm.upsample:
                        parm.upsample = Var(make_temp_name(), parm)
                        parm.upsample.rate = BR
                        print("created variable for", str(parm))
                    ugen.parameters[i] = parm.upsample
                    print("replaced parameter", i, "in", str(ugen), "with",
                          str(parm.upsample))
            # CR expressions that are computed should be saved in a temp
            elif parm.rate == CR and ugen.rate == AR and \
                 type(parm) != Ugen and not isinstance(parm, Var):
                if not parm.upsample:
                    parm.upsample = Var(make_temp_name(), parm)
                    parm.upsample.rate = CR
                    print("created variable for", str(parm))
                ugen.parameters[i] = parm.upsample
                print("replaced parameter", i, "in", str(ugen), "with",
                      str(parm.upsample))


    # now that we've added Upsample ugens, recompute
    ugens = out.get_ugen_list()

#    print_ugens("ugens including Upsample", ugens)

    print("*************************")
    out.print_tree()
    print("*************************")

    name += "_" + out.rate
    ratestring = "".join(rates)  # make one string to be hashable
    variations[ratestring] = (name + "_create", out.rate)
    print("class ", name, " : Ugen_out", out.rate, " {", sep="")

    # declare member variables
    for ugen in ugens:
        ugen.gen_declarations()

    # generate constructor
    print("\n    void ", name, "(", sep="", end="")
    need_comma = False
    for i in range(len(params)):
        if need_comma:
            print(", ", sep="", end="")
        print(RATE_TO_TYPE[rates[i]], params[i].name, sep="", end="")
        need_comma = True
    print(") {\n        block_count = 0;")
    for ugen in ugens:
        ugen.gen_constructor()
    print("    }")

    # generate run() method
    print("\n    void run(long block_num) {")
    # update inputs
    for ugen in ugens:
        ugen.gen_update_input()
    print("        block_count = block_num;")

    #   get pointers to samples for AR inputs
    for ugen in ugens:
        ugen.gen_brate_code()

    for ugen in ugens:
        ugen.gen_upsample_prep()

    #   generate inner loop of run() method if rate is AR
    if out.rate == AR:
        print("        for (int i = 0; i < BL; i++) {")
        for ugen in ugens:
            ugen.gen_arate_code()
        print("            out[i] = ", out.gen_code(), ";", sep="")
        #   generate next state values
        for ugen in ugens:
            ugen.gen_next_arate_state()
        #   generate BR updates
        for ugen in ugens:
            ugen.gen_upsample_update()
        #   generate state updates
        for ugen in ugens:
            ugen.update_arate_state()

        print("        }", sep="")
    elif out.rate == BR:
        print("        out = ", out.gen_code(), ";", sep="")

    # generate next state values
    for ugen in ugens:
        ugen.gen_next_state_br()
    #   generate state updates
    for ugen in ugens:
        ugen.update_state_br()
    print("    }\n};\n")


def make_rate_combinations(rates, commutative):
    result = make_all_combinations(rates, commutative)
    # remove CR-only
    final = []
    print("result", result)
    for r in result:
        if min(r) != CR:
            final.append(r)
    print("make_rate_combinations", rates, commutative, final)
    return final


def make_all_combinations(rates, commutative):
    first = rates[0]  # e.g. "AB"
    all = [[r] for r in first]
    result = all
    if len(rates) > 1:
        rest = make_all_combinations(rates[1:], commutative)
        # for each element in all, splice each element in rest
        print("all", all, "rest", rest)
        result = []
        for r1 in all:
            for r in rest:
                if commutative and r1[0] > r[0][0]:
                    continue
                result.append(r1 + r)
    return result


# print("test", make_all_combinations(["abc"], True))


# [AR+BR, AR+BR+CR], [pa, pb], pa * pb)
def ugg_generate(rates, parms, expr, commutative=False):
    global variations
    print("ugg_generate", rates, parms, expr, commutative)
    rates = make_rate_combinations(rates, commutative)
    for r in rates:
        ugg_write(r, parms, expr, min(rates))
    # now generate declaration for Python
    print("*********************************************")
    print(ugg_name, "_implementations = ", repr(variations), sep="")
    print("class", ugg_name, "(Patch):")
    print("    def __init__(", end="")
    for i in range(len(parms)):
        print("p", str(i + 1), ", ", sep="", end="")
    print("name=None):")
    if commutative:  # assume two parameters if commutative
        print("        # assumes at least one parameter is a Patch")
        print("        # sort by Patch")
        print("        if not isinstance(p1, Patch):")
        print("            temp = p1")
        print("            p1 = p2")
        print("            p2 = p1")
        print("        elif not isinstance(p2, Patch):")
        print("            if p1.rate == BR:")
        print("                temp = p1")
        print("                p1 = p2")
        print("                p2 = p1")
        print("        rates = p1.rate + p2.rate")
    else:
        print("        rates = ")
        need_plus = False
        for i in range(len(parms)):
            print(" + " if need_plus else "", "p", str(i + 1), ".rate",
                  sep="", end="")
            need_plus = True
        print()
    print("        # find matching implementation")
    print("        impl = ", ugg_name, "_implementations[rates]", sep="")
    for i in range(len(parms)):
        print("        if isinstance(p", str(i + 1), ", Patch):", sep="")
        print("            self.insert_patch(p", str(i + 1), ")", sep="")
    print("        instr = impl[0](", end="")
    for i in range(len(parms)):
        print("p", str(i + 1), ", ", sep="", end="")
    print("audio_space_zone)")
    print("        super().__init__(instr, 1, impl[1], name)")


# ---------
AR = 'a'
BR = 'b'
CR = 'c'

ugg_begin("Math")
px = Param("x")
py = Param("y")
pz = Param("z")
Var("yval", py)
math = Var("temp", (px + "yval") * pz)
# print("Ugen List: ", math.get_ugen_list())

math.print_tree()
print()
ugg_write([AR, CR, AR], [px, py, pz], math, AR)
ugg_write([AR, BR, BR], [px, py, pz], math, AR)
ugg_write([AR, AR, AR], [px, py, pz], math, AR)
ugg_write([BR, BR, BR], [px, py, pz], math, BR)


# a component that does a simple smoothing of an input signal
#
def smooth(x):
    sm = First(make_temp_name(), 0)
    Next(sm, sm * 0.9 + x * 0.1)
    return sm

ugg_begin("Smooth")
px = Param("x")
ugg_write([BR], [px], smooth(px), BR)

ugg_begin("Osc")
sine_table = Ugen("sine_table")
pfreq = Param("freq")
phase_incr = pfreq * Ugen("SR_RECIP")
indexf = First("indexf", 0)
index = Var("index", Uint(indexf))
x1 = Var("x1", sine_table[index])
Next(indexf, Ufmodf(indexf + phase_incr, Ugen("TABLE_LEN")))
osc = x1 + (indexf - index) * (sine_table[index + 1] - x1)
indexf.use_output_rate()
phase_incr.use_non_interpolated()
osc.print_tree()
print()
ugg_write([CR], [pfreq], osc, AR)
ugg_write([BR], [pfreq], osc, AR)

# ---------

def oscf(pfreq):
    sine_table = Ugen("sine_table")
    phase_incr = pfreq * Ugen("SR_RECIP")
    indexf = First("indexf", 0)
    index = Var("index", Uint(indexf))
    x1 = Var("x1", sine_table[index])
    Next(indexf, Ufmodf(indexf + phase_incr, Ugen("TABLE_LEN")))
    osc = x1 + (indexf - index) * (sine_table[index + 1] - x1)
    indexf.use_output_rate()
    phase_incr.use_non_interpolated()
    return osc
    

ugg_begin("Osc")
pfreq = Param("freq")
ugg_write([CR], [pfreq], oscf(pfreq), AR)
ugg_write([BR], [pfreq], oscf(pfreq), AR)

ugg_write([BR], [pfreq], oscf(smooth(pfreq)), AR)


ugg_begin("Mult")
pa = Param("a")
pb = Param("b")
#ugg_write([AR, AR], [pa, pb], pa * pb, AR)
#ugg_write([AR, BR], [pa, pb], pa * pb, AR)
ugg_generate([AR+BR, AR+BR+CR], [pa, pb], pa * pb, commutative=True)


ugg_begin("Phasor")
freq = Param("freq")
phase = First("phase", 0, "double")
phase.use_output_rate()
Next(phase, Ufmod(phase + freq / SR, 1))
ugg_write([CR], [freq], phase, AR)

# test

def foo():
    print(123)


print("test 1")
expr = Ugen(100) + Ugen(200)
expr.print_tree()

print("test 2")
expr = Ugen(100) + Ugen(200) + 5 + Param("input")
expr.print_tree()
print(expr.gen_code())
# print_ugens("Ugen List", expr.get_ugen_list())
