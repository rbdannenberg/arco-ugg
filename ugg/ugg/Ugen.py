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

from cmake import *


UGG_INDENT = 2
UGG_STATE = "ugg_state"
SAMPLE_TYPE = "float"

def isfloat(typespec):
    return typespec == "float" or \
           (SAMPLE_TYPE == "float" and typespec == "sample")

def error(*args):
    print("\n**** ERROR: ", end="")
    for arg in args:
        print(str(arg), sep=" ", end="")
    print(" ****")
    get_a_stack_trace()


CODE_PATH = "code/"

def ug_indent(depth):
    if depth == 1:
        depth = 0
    print(" " * depth * UGG_INDENT, end="")

# force rate to be block rate, e.g. for an lfo, write brate(osc(...))
#
def brate(ugen):
    ugen.rate = BR
    return ugen

def once(ugen):
    ugen.rate = CR
    return ugen

def zipper(ugen):
    ugen.rate = BR
    ugen.interpolate_ok = False
    return ugen


class Ugen:
    def __init__(self, value=None, typespec="sample"):
        if value != None:
            self.op = "const"
            self.value = value
            self.typespec = typespec
        self.parameters = []
        self.visited = False
        self.upsample = False
        self.interpolate_ok = True
        self.output_rate = False
        self.rate = None
        self.name = None
        self.details = "" # how did we get our rate?

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
        dest.details = self.details
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
        return Uadd(self, right)

    def __radd__(self, left):
        return Uadd(self, left)

    def __sub__(self, right):
        return Usubtract(self, right)

    def __rsub__(self, left):
        return Usubtract(Ugen(left), self)

    def __mul__(self, right):
        return Umul(self, right)

    def __rmul__(self, left):
        return Umul(self, left)

    def __truediv__(self, right):
        return Udiv(self, right)

    def __rtruediv__(self, left):
        return Udiv(Ugen(left), self)

    def __lt__(self, right):
        return Ulessthan(self, right)

    def __getitem__(self, key):
        return Usubscript(self, key)

    def print_tree(self):
        global to_be_printed
        global printed
#        print("adding", self, "to to_be_printed")
        to_be_printed = [self]
        printed = []
        expr_count = 1
        while len(to_be_printed) > 0:
            to_print = to_be_printed[-1]
            printed.append(to_print)
            print(expr_count, ") ", sep="", end="")
            expr_count += 1
            to_print.print_subtree(1)
            to_be_printed.remove(to_print)

    def print_self(self, depth, text):
        up = str(self.upsample) if self.upsample else ""
        ug_indent(depth)
        print(text, " rate: ", self.rate, " (", self.details, \
              ") typespec: ", self.typespec, sep="")
        if up: 
            ug_indent(depth)
            print("up:", up)

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

    # recursive helper function - returns topologically sorted list
    # of ugens, with dependent ugens later in the list
    def get_ugen_list2(self, depth):
        ug_indent(depth)
        print("get_ugen_list2 called", self)
        ugens = []
        self.visited = True
        for ugen in self.get_all_parameters():
            if not ugen.visited:
                new_ugens = ugen.get_ugen_list2(depth + 1)
                ugens = ugens + new_ugens
        ugens.append(self)
        ug_indent(depth)
        print("get_ugen_list2 returns", end="")
        for u in ugens:
            print(u, end="")
        print()
        return ugens

    def use_output_rate(self):
        self.output_rate = True

    def use_non_interpolated(self):
        self.interpolate_ok = False

    def found_rate(self, details):
        # used for debugging, you can print something here
        return True

    def find_rate(self, out_rate):
        details = "" # used for debugging/reporting how rate determined
        if self.output_rate:
            details = "output_rate is set"
            self.rate = out_rate
        if not self.rate:
            self.rate = CR
            details = "default is CR"
            for ugen in self.parameters:
                if ugen.find_rate(out_rate) < self.rate:
                    details = "got rate from a parameter"
                    self.rate = ugen.rate  # go as fast as any we depend on
        if self.rate == CR and isinstance(self, First):
            details = "state variable is at least block rate"
            self.rate = BR  # 
        self.found_rate(details)
        # oh heck, let's store all the details and print them out in the tree
        if details != "":
            self.details = details
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


class Cond (Ugen):
    def __init__(self, test, left, right):
        global ugg_vars
        super().__init__()
        right = coerce_to_ugen(right, "Cond")
        self.parameters.append(test)
        self.parameters.append(left)
        self.parameters.append(right)
        # left and right are not in parameters and are only
        # evaluated conditionally
        self.left = left
        self.right = right
        assert(left.typespec)
        assert(right.typespec)
        assert(left.typespec == right.typespec)
        self.typespec = left.typespec

    def copy(self):
        new = Cond(self.parameters[0], self.left, self.right)
        return self.copy_fields_to(new)

    def __str__(self):
        return "<Cond>"

    def print_subtree(self, depth):
        self.print_self(depth, "cond")
        depth += 1
        param = self.parameters[0]
        if isinstance(param, Ugen):
            param.print_subtree(depth)
        else:
            print("SURPRISE! the test is not a Ugen")
            ug_indent(depth)
            print(param)
        self.left.print_subtree(depth)
        self.right.print_subtree(depth)

    def gen_code(self):
        return "(" + self.parameters[0].gen_code() + " ? " + \
               self.left.gen_code() + " : " + \
               self.right.gen_code() + ")"

        
class Ubinary (Ugen):
    def __init__(self, op, left, right):
        global ugg_vars
        super().__init__()
        self.op = op
        right = coerce_to_ugen(right, op)
        self.parameters.append(left)
        # print("in Ubinary.__init__, left", left, "right", right)
        if type(right) == str:
            error("bad right value for Ubinary " + op)
        self.parameters.append(right)
        # print("Ubinary init", op, left, right)
        assert(left.typespec)
        assert(right.typespec)
        # type: if an arg is sample, result is sample
        #       else if an arg is double, result is double
        #       else if an arg is float result is float
        #       else result is type of first argument
        # (these might not be the right rules, but they've worked
        #  so far)
        if left.typespec == "sample" or \
             right.typespec == "sample": \
               self.typespec = "sample" 
        elif left.typespec == "double" or \
             right.typespec == "double": \
               self.typespec = "double" 
        elif left.typespec == "float" or \
             right.typespec == "float": \
               self.typespec = "float" 
        else:
             self.typespec = left.typespec


    def copy(self):
        return self.copy_fields_to(Ubinary(self.op, self.parameters[0],
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
            ug_indent(depth)
            print(self.parameters[0])

        if isinstance(self.parameters[1], Ugen):
            self.parameters[1].print_subtree(depth)
        else:
            print("SURPRISE! right operand is not a Ugen")
            ug_indent(depth)
            print(self.parameters[1])

    def gen_code(self):
        return "(" + self.parameters[0].gen_code() + " " + self.op + " " + \
               self.parameters[1].gen_code() + ")"


class Uunary (Ugen):
    def __init__(self, op, param, typespec=None):
        global ugg_vars
        super().__init__()
        self.op = op
        self.typespec = typespec if typespec else param.typespec
        self.parameters.append(coerce_to_ugen(param, op))

    def copy(self):
        return self.copy_fields_to(Uunary(self.op, self.parameters[0]))

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
            ug_indent(depth)
            print(param)

    def gen_code(self):
        return self.op + "(" + self.parameters[0].gen_code() + ")"


class Ufn2 (Ugen):
    def __init__(self, op, p1, p2, typespec=None):
        global ugg_vars
        super().__init__()
        self.op = op
        p1 = coerce_to_ugen(p1, op)
        p2 = coerce_to_ugen(p2, op)
        self.parameters.append(p1)
        self.parameters.append(p2)
        self.typespec = typespec if typespec else \
                        ("double" if p2.typespec == "double" else \
                         p1.typespec)

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
            ug_indent(depth)
            print(param)

        param = self.parameters[1]
        if isinstance(param, Ugen):
            param.print_subtree(depth)
        else:
            print("SURPRISE! the operand is not a Ugen")
            ug_indent(depth)
            print(param)

    def gen_code(self):
        return self.op + "(" + self.parameters[0].gen_code() + ", " + \
               self.parameters[1].gen_code() + ")"


class Usubscript (Ugen):
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
        self.typespec = "sample" # should depend on array declaration

    def copy(self):
        new = Usubscript(self.table, self.index)
        return self.copy_fields_to(new)

    def __str__(self):
        return "<Subscript " + str(self.table) + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "subscript")
        depth += 1

        if isinstance(self.table, Ugen):
            self.table.print_subtree(depth)
        else:
            ug_indent(depth)
            print(self.table)

        if isinstance(self.index, Ugen):
            self.index.print_subtree(depth)
        else:
            ug_indent(depth)
            print(self.index)

    def gen_code(self):
        return "tblget(" + self.table.gen_code() + ", " + \
               self.index.gen_code() + ")"


class Uadd (Ubinary):
    def __init__(self, left, right):
        super().__init__("+", left, right)


class Usubtract (Ubinary):
    def __init__(self, left, right):
        super().__init__("-", left, right)


class Umul (Ubinary):
    def __init__(self, left, right):
        super().__init__("*", left, right)

class Udiv (Ubinary):
    def __init__(self, left, right):
        super().__init__("/", left, right)

class Ulessthan (Ubinary):
    def __init__(self, left, right):
        super().__init__("<", left, right)

# phase_wrap should be a macro as follows:
#   while (phase >= table_len) phase -= table_len
#
class Uphasewrap (Ufn2):
    def __init__(self, phase, table_len):
        super().__init__("phase_wrap", phase, table_len, "double")


# table_len should be a macro as follows:
#   table->size - 1
# tables are stored with a redundant copy of the first
#   element at the end, hence table_len is size - 1
#
class Utable_len(Uunary):
    def __init__(self, table):
        super().__init__("table_len", table, "int")


class Uint (Uunary):
    def __init__(self, param):
        super().__init__("int", param, "int")


class Ufmodf (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmodf", p1, p2)


class Ufmod (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmod", p1, p2)


class Umax (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmax", p1, p2)


class Umin (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("fmin", p1, p2)


class Upow (Ufn2):
    def __init__(self, p1, p2):
        super().__init__("pow", p1, p2)


class Uabs (Uunary):
    def __init__(self, param):
        super().__init__("fabs", param)


# The idea here was to generate both AR and BR versions
# of generators, but the problem is how do you know which
# one to use? We'll use ARGEN and BRGEN instead, specifying
# a particular output rate, and use differnet names, e.g.
# LFO and OSC to select which output rate you want.
#
#def GEN(*params):
#    return list(params) + [GR+AR+BR]


def ARGEN(*params):
    return list(params) + [GR+AR]


def BRGEN(*params):
    return list(params) + [GR+BR]


def FILTER(*params):
    return list(params) + [FR]


# given a Param and a rate, compute the type
def typespec_for_rate(param, rate):
    print("typespec_for_rate", param.name, param.typespec, rate)
    if param.typespec == "float" or param.typespec == "sample":
        return RATE_TO_TYPE[rate]
    elif rate == CR:
        print("typespec returns", param.typespec)
        return param.typespec + " "
    elif param.typespec == "double":
        return RATE_TO_TYPE[rate] # double treated like float here
    else:
        error("param typespec given, but it is not C rate: " + 
              str(param))


class Param (Ugen):
    def __init__(self, name, typespec="sample"):
        super().__init__()
        self.op = "param"
        self.name = name
        self.rate = CR
        self.typespec = typespec;
        self.actions = []
        print("Param __init__", typespec, self.typespec)

    def copy(self):
        new = self.copy_fields_to(Param(self.name))
        new.typespec = self.typespec
        return new

    def __str__(self):
        return "<Param " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "parameter " + self.name)

    def update(self, state, expr):
        self.actions.append([state, expr])

    def gen_code(self):
        if self.rate == AR:
            return self.name + "_samps[i]"
        elif self.rate == BR:
            return self.name + "->get_out()"
        else:
            return self.name

    def gen_declarations(self):
        # default for parameters is float type, but if the rate
        # is AR or BR, the parameter is a Ugen *. If the rate is
        # CR, there can be another user-provided type in typespec.
        typespec = typespec_for_rate(self, self.rate)
        print("    ", typespec, self.name, ";", sep="", file=hdrf)

    def gen_update_input(self):
        if self.rate == CR:
            return
        print("    if (", self.name, "->block_count < block_num) {", sep="",
              file=srcf)
        print("        ", self.name, "->run(block_num);", sep="", file=srcf)
        print("    }", file=srcf)

    def gen_brate_code(self):
        if self.rate == AR:
            print("    sample *", self.name, "_samps = ",
                  self.name, "->get_outs();", sep="", file=srcf)

    def gen_constructor(self):
        print("    this->", self.name, " = ", self.name, ";", 
              sep="", file=srcf)


class Var (Ugen):
    def __init__(self, name, value, typespec=None):
        global ugg_vars
        super().__init__()
        self.op = "var"
        self.name = name
        self.parameters = [coerce_to_ugen(value, "Var initialization")]
        self.typespec = typespec if typespec else value.typespec
        assert(type(self.typespec) == str)
        print("in Var, name", name, "typespec", self.typespec)
        ugg_vars[name] = self
        ugg_ordered_vars.append(self)


    def found_rate(self, details):
        # DEBUG:
        if self.name == "oscval" or self.name == "osc_index":
            print("found_rate for", self.name, ":", self.rate, details)

    def copy(self):
        return self.copy_fields_to(Var(self.name, self.parameters[0],
                                       self.typespec))

    def __str__(self):
        return "<Var " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "Var: " + self.name)
        if depth == 1:
            self.parameters[0].print_subtree(depth + 1)
        elif self not in to_be_printed and self not in printed:
            to_be_printed.append(self)

    def gen_declarations(self):
        if self.rate == CR:
            print("    ", self.typespec, " ", self.name, ";", 
                  sep="", file=hdrf)

    def gen_constructor(self):
        if self.rate == CR:
            print("    ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="", file=srcf)

    def gen_brate_code(self):
        if self.rate == BR:
            print("    ", self.typespec, " ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="", file=srcf)

    def gen_arate_code(self):
        if self.rate == AR:
            print("        ", self.typespec, " ", self.name, " = ",
                  self.parameters[0].gen_code(), ";", sep="", file=srcf)

    def gen_code(self):
        return self.name


class First (Var):
    def __init__(self, name, value, typespec=None):
        super().__init__(name, value)
        self.typespec = typespec if typespec else value.typespec
        self.rest = None

    def copy(self):
        new = self.copy_fields_to(First(self.name, self.parameters[0],
                                        self.typespec))
        new.rest = self.rest
        new.typespec = self.typespec
        return new

    def update_refs(self, old_to_new):
        super().update_refs(old_to_new)
        self.rest = old_to_new[self.rest]

    def __str__(self):
        return "<State " + self.name + ">"

    def print_subtree(self, depth):
        self.print_self(depth, "State: " + self.name + " " + self.typespec)
        if depth == 1:
            self.parameters[0].print_subtree(2)
            self.rest.print_subtree(2)
        elif self not in to_be_printed and self not in printed:
            # print("adding", self, "to to_be_printed")
            to_be_printed.append(self)

    # This overrides get_all_parameters() in Ugen -- this is a special case
    # because First is specified by both First() and Next(), indicating
    # initialization and each successive value, computed at audio or block rate
    def get_all_parameters(self):
        if not self.rest:
            error("State was created with First, but Next was not called",
                  "to finish the definition")
        return self.parameters + [self.rest]

    def gen_declarations(self):
        print("    ", self.typespec, " ", self.name, ";", sep="", file=hdrf)

    def gen_constructor(self):
        print("    ", self.name, " = ",
              self.parameters[0].gen_code(), ";", sep="", file=srcf)

    def gen_brate_code(self):  # overrides Var.gen_brate_code
        return

    def gen_arate_code(self):  # overrides Var.gen_arate_code
        return

    def gen_next_arate_state(self):
        if self.rate != AR:
            return None
        print("        ", self.typespec, " ", self.name, "_next = ", 
              self.rest.gen_code(), ";", sep="", file=srcf)

    def gen_next_state_br(self):
        if self.rate != BR:
            return None
        print("    ", self.typespec, " ", self.name, "_next = ",
              self.rest.gen_code(), ";", sep="", file=srcf)

    def update_arate_state(self):
        if self.rate != AR:
            return None
        print("        ", self.name, " = ", self.name, "_next;", 
              sep="", file=srcf)

    def update_state_br(self):
        if self.rate != BR:
            return None
        print("    ", self.name, " = ", self.name, "_next;", 
              sep="", file=srcf)


def Next(var, defn):
    global ugg_vars
    if type(var) == str:
        var = ugg_vars[var]
    if not isinstance(var, First):
        error(str(var) + " in Next should be an instance of First.")
    var.rest = defn


# special First that forces rate to be AR, e.g. to count samples
class FirstAR (First):
    def __init__(self, name, value, typespec=None):
        super().__init__(name, value, typespec)
        self.output_rate = AR


tempnum = 0

def make_temp_name():
    global tempnum
    tempnum += 1
    return "t" + str(tempnum)


class Upsample (Uunary):
    def __init__(self, what):
        super().__init__("upsamp", what)
        self.name = make_temp_name()
        self.rate = AR

    def copy(self):
        return self.copy_fields_to(Upsample(self.parameters[0]))

    def __str__(self):
        return "<Upsample " + self.name + ">"

    def gen_upsample_prep(self):
        print("    sample ", self.name, "_step = (", 
              self.parameters[0].gen_code(), " - ", self.gen_code(), 
              ") * BR_RECIP;", sep="", file=srcf)

    def gen_code(self):
        return self.name + "_arate"

    def gen_declarations(self):
        print("    sample ", self.name, "_arate;", sep="", file=hdrf)

    def gen_constructor(self):
        print("    ", self.name, "_arate = 0;", sep="", file=srcf)

    def gen_upsample_update(self):
        print("            ", self.name, "_arate += ", self.name, "_step;",
              sep="", file=srcf)

# ---------


RATE_TO_TYPE = {'a': "Ugen *", 'b': "Ugen *", 'c': "sample "}

AR = Ugen("AR")

def ugg_begin(name):
    global ugg_name, ugg_vars, ugg_ordered_vars
    global AR, variations, hdrf, srcf
    ugg_name = name
    ugg_vars = {}  # mapping from strings to Var objects
    ugg_ordered_vars = []
    variations = {}
    name = name.lower()

    hdrf = open(CODE_PATH + name + ".h", "w")
    print("//", name, "declarations\n", file=hdrf)

    srcf = open(CODE_PATH + name + ".cpp", "w")
    print("//", name, "implementations\n", file=srcf)
    print('#include "ugen.h"', file=srcf)
    print('#include "', name, '.h"', sep="", file=srcf)

    set_source_path(CODE_PATH)
    add_source_files(name + ".h", name + ".cpp")


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
    global ugg_name, variations, hdrf, srcf

    print("#### ugg_write", ugg_name, rates, params, rate)
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
                    print("replaced (A) parameter", i, "in", str(ugen), "with",
                          str(parm.upsample))
                elif not isinstance(parm, Var):
                    # capture computation in a var at brate, access at arate
                    if not parm.upsample:
                        parm.upsample = Var(make_temp_name(), parm)
                        parm.upsample.rate = BR
                        print("created variable for", str(parm))
                    ugen.parameters[i] = parm.upsample
                    print("replaced (B) parameter", i, "in", str(ugen), "with",
                          str(parm.upsample))
            # CR expressions that are computed and used in run()
            # should be saved in a temp. If the CR expression is
            # a Var or Param, there's no need for a copy of it.
            # If the CR expression is parameter 0 (initialization) 
            # of First (state), then do not create a temp variable. 
            elif parm.rate == CR and ugen.rate == AR and \
                 type(parm) != Ugen and not isinstance(parm, Var) \
                 and not isinstance(parm, Param) \
                 and not (i == 0 and isinstance(ugen, First)):
                if not parm.upsample:
                    parm.upsample = Var(make_temp_name(), parm)
                    parm.upsample.rate = CR
                    print("created variable for", str(parm))
                ugen.parameters[i] = parm.upsample
                print("replaced (C) parameter", i, "=", parm, "in", str(ugen), \
                      "with", str(parm.upsample))


    # now that we've added Upsample ugens, recompute
    ugens = out.get_ugen_list()

#    print_ugens("ugens including Upsample", ugens)

    print("*************************")
    out.print_tree()
    print("*************************")

    name += "_" + out.rate
    ratestring = "".join(rates)  # make one string to be hashable
    variations[ratestring] = (name + "_create", out.rate)
    print("class ", name, " : public Ugen_out", out.rate, " {", 
          sep="", file=hdrf)

    # declare member variables
    for ugen in ugens:
        ugen.gen_declarations()

    # generate constructor
    print("\n  public:", file=hdrf)
    print("    ", name, "(", sep="", end="", file=hdrf)
    print("\n", name, "::", name, "(", sep="", end="", file=srcf)
    need_comma = False
    for i in range(len(params)):
        if need_comma:
            print(", ", sep="", end="", file=hdrf)
            print(", ", sep="", end="", file=srcf)
        param_typespec = typespec_for_rate(params[i], rates[i])
        print(param_typespec, params[i].name, sep="", end="", file=hdrf)
        print(param_typespec, params[i].name, sep="", end="", file=srcf)
        need_comma = True
    print(");", file=hdrf)
    print(")\n{\n    block_count = 0;", file=srcf)
    for ugen in ugens:
        ugen.gen_constructor()
    print("}", file=srcf)

    # generate run() method
    print("    void run(long block_num);", file=hdrf)
    print("\nvoid ", name, "::run(long block_num)\n{", file=srcf, sep="")
    # update inputs
    for ugen in ugens:
        ugen.gen_update_input()
    print("    block_count = block_num;", file=srcf)

    #   get pointers to samples for AR inputs
    for ugen in ugens:
        ugen.gen_brate_code()

    for ugen in ugens:
        ugen.gen_upsample_prep()

    #   generate inner loop of run() method if rate is AR
    if out.rate == AR:
        print("    for (int i = 0; i < BL; i++) {", file=srcf)
        # currently, we only generate code for Vars, and we do so
        # in the order of Var creation -- user is expected to 
        # order Var declarations so that Vars are defined before use
        count = 1
        for ugen in ugens:
            print("Ugens[" + str(count) + "] =", ugen, end=" ")
            for p in ugen.parameters:
                print(p, end="")
            print()
            count += 1
        for ugen in ugens:
            ugen.gen_arate_code()
        print("        outs[i] = ", out.gen_code(), ";", sep="", file=srcf)
        #   generate next state values
        for ugen in ugens:
            ugen.gen_next_arate_state()
        #   generate BR updates
        for ugen in ugens:
            ugen.gen_upsample_update()
        #   generate state updates
        for ugen in ugens:
            ugen.update_arate_state()

        print("    }", sep="", file=srcf)
    elif out.rate == BR:
        print("    out = ", out.gen_code(), ";", sep="", file=srcf)

    # generate next state values
    for ugen in ugens:
        ugen.gen_next_state_br()
    #   generate state updates
    for ugen in ugens:
        ugen.update_state_br()
    print("}", file=srcf)

    # now write update actions
    # when a "constant" parameter is updated, change the state 
    # variables to new values
    for param in params:
        if param.actions:
            print("    void set_", param.name, "(sample ",
                  param.name, ");", sep="", file=hdrf)
            print("void ", name, "::set_", param.name, "(sample ",
                  param.name, ") {", sep="", file=srcf)
            for action in param.actions:
                statevar = action[0]
                newval = action[1]
                print("    ", statevar.name, " = ",
                      newval.gen_code(), ";", sep="", file=srcf)
            print("}", file=srcf)
    print("};\n", file=hdrf)


# prates represents all parameter rates. Determine possible output
# rates (AR and/or BR) by looking at r
#
# returns "", "a", "b", or "ab"
#
def filter_rates_from_params(prates):
    arate = ""
    brate = ""
    for rates in prates:
        if AR in rates: arate = AR
        if BR in rates: brate = BR
    print("filter_rates_from_params", arate + brate)
    return arate + brate # concatenate maybe "a" and maybe "b"


def make_rate_combinations(rates, commutative):
    print("mrc", rates, commutative)
    param_rates = rates[0 : -1]
    output_type = rates[-1]
    if output_type[0] == 'g':
        # generators: use the single output type specified
        rates = param_rates + [output_type[1]]
    else:
        rates = param_rates + [filter_rates_from_params(param_rates)]

    result = make_all_combinations(rates, commutative)
    print("mrc2", output_type, rates, commutative, result)

    # If this is a filter, output rate was marked "f", and output
    # should be the max of any input rate
    # If this is a generator, output rate was marked "g", then
    # only requirements is for the output rate to be as high as any
    # input. If this is a processor, The output should the max rate
    # of inputs, and therefore inputs cannot all be CR.
    final = []
    if output_type[0] == FR:
        print("result", result)
        for r in result:
            out_rate = max(r[0 : -1])
            actual_out_rate = r[-1]
            if out_rate == actual_out_rate:
                final.append(r)
    else:
        assert(output_type[0] == GR)
        for r in result:
            min_out_rate = max(r[0 : -1])
            actual_out_rate = r[-1]
            if min_out_rate >= actual_out_rate:
                final.append(r)
            print("mrcloop", min_out_rate, actual_out_rate, final)
    print("make_rate_combinations", rates, commutative, final)
    return final        


def make_all_combinations(rates, commutative):
    print("make_all_combinations", rates)
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
        ugg_write(r[0 : -1], parms, expr, r[-1])
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
    hdrf.close()
    srcf.close()


AR = 'a'
BR = 'b'
CR = 'c'
FR = 'f'
GR = 'g'
