"""
Translate a Python script into assembly for
Ben Eater's SAP computer

Inspired from https://github.com/benhoyt/pyast64
"""

import ast


SCRIPT = (
    "x = 0\n"
    "while True:\n"
    "    x += 3\n"
    "    print(x)\n"
)

VARS = {}
LABELS = []


class Instruction:
    def __init__(self, opcode, operand=None, label=None):
        self.opcode = opcode
        self.operand = operand
        self.label = label

    def __str__(self):
        line = self.opcode
        if self.operand is not None:
            line += f" {self.operand}"
        return line


class Compiler:
    def __init__(self):
        self._next_var_location = 15
        self._assembly = []

    @property
    def next_var_location(self):
        return self._next_var_location

    @next_var_location.setter
    def next_var_location(self, new_val):
        if 0 > new_val > 15:
            raise ValueError("Not enough memory to store value")
        self._next_var_location = new_val

    def compile(self, node):
        assembly = []
        self.visit(node)
        self._assembly.append(Instruction("HLT"))
        self.optimize()

        # replace labels
        for index, instruction in enumerate(self._assembly):
            if instruction.opcode == "LABEL":
                self._assembly[index + 1].label = instruction.label
        for instruction in self._assembly:
            if instruction.operand in LABELS:
                for line_number, inner_instruction in enumerate([i for i in self._assembly if i.opcode != "LABEL"]):
                    if inner_instruction.label == instruction.operand:
                        instruction.operand = line_number
                        break

        for index, instruction in enumerate([i for i in self._assembly if i.opcode != "LABEL"]):
            assembly.append(f"{index} {instruction}")
        lines = "\n".join(assembly)
        if len(assembly) + len(VARS) > 16:
            raise ValueError(f"\n{lines}\nProgram doesn't fit into memory")
        return lines

    def optimize(self):
        instructions = self._assembly
        optimized_instructions = self._optimize_accumulator_use(instructions)
        optimized_instructions = self._optimize_jumps(optimized_instructions)
        self._assembly = optimized_instructions

    def _optimize_accumulator_use(self, instructions):
        """if we have a "STA n" directly followed by a "LDA n", then
        we can delete the LDA since the value is still in the A register
        """
        optimized_instructions = [instructions[0]]
        previous_instruction = instructions[0]
        for instruction_index, instruction in enumerate(instructions):
            if instruction_index == 0:
                continue
            if instruction.opcode == "LDA" and previous_instruction.opcode in ["STA", "DSP"]:
                if instruction.operand == previous_instruction.operand and not instruction.label:
                    continue
            optimized_instructions.append(instruction)
            previous_instruction = instruction
        return optimized_instructions

    def _optimize_jumps(self, instructions):
        """If we have a JMP N on line N-1, then we can just omit the jump"""
        optimized_instructions = [instructions[0]]
        for instruction_index, instruction in enumerate(instructions):
            if instruction_index == 0:
                continue
            if instruction.opcode == "JMP" and instruction.operand == instructions[instruction_index + 1].label:
                continue
            optimized_instructions.append(instruction)
        return optimized_instructions

    def next_label(self):
        if not LABELS:
            LABELS.append("label_0")
        else:
            LABELS.append(f"label_{int(LABELS[-1].split('_')[1]) + 1}")
        return LABELS[-1]

    def visit(self, node):
        # We could have subclassed ast.NodeVisitor, but it's better to fail
        # hard on AST nodes we don't support
        name = node.__class__.__name__
        visit_func = getattr(self, 'visit_' + name, None)
        assert visit_func is not None, '{} not supported - node {}'.format(
                name, ast.dump(node))
        visit_func(node)

    def visit_Module(self, node):
        for statement in node.body:
            self.visit(statement)

    def visit_Assign(self, node):
        assert len(node.targets) == 1, "Can only assign 1 value at a time"

        target = node.targets[0]
        if target.id in VARS:
            target_location = VARS[target.id]
        elif target.id != "A_REG":
            target_location = self.next_var_location
            VARS[target.id] = target_location
            self.next_var_location -= 1

        if isinstance(node.value, ast.Num):
            value = node.value.n
            assert value < 16, "Cannot store value > 15"
            self._assembly.append(Instruction("LDI", operand=value))
        elif isinstance(node.value, ast.BinOp):
            if isinstance(node.value.left, ast.Num):
                self._assembly.append(Instruction("LDI", operand=node.value.left.n))
            else:
                var_location = VARS[node.value.left.id]
                self._assembly.append(Instruction("LDA", operand=var_location))
            if isinstance(node.value.right, ast.Num):
                self._assembly.append(Instruction("INC", operand=node.value.right.n))
            else:
                var_location = VARS[node.value.right.id]
                self._assembly.append(Instruction("ADD", operand=var_location))
        else:
            assert node.value.id in VARS, f"Cannot find address of {node.value.id}"
            var_location = VARS[node.value.id]
            self._assembly.append(Instruction("LDA", operand=var_location))

        self._assembly.append(Instruction("STA", operand=target_location))

    def visit_AugAssign(self, node):
        assert node.target.id in VARS, f"{node.target.id} is not defined in VARS"
        var_location = VARS[node.target.id]
        self._assembly.append(Instruction("LDA", operand=var_location))

        if isinstance(node.value, ast.Name):
            assert node.value.id in VARS, f"{node.value.id} is not defined in VARS"
            var_location = VARS[node.value.id]
            self._assembly.append(Instruction("ADD", operand=var_location))
        else:
            self._assembly.append(Instruction("INC", operand=node.value.n))

        self._assembly.append(Instruction("STA", operand=var_location))


    def visit_While(self, node):
        if isinstance(node.test, ast.NameConstant):
            if node.test.value is False:
                return
        current_label = self.next_label()
        self._assembly.append(Instruction("LABEL", label=current_label))
        for statement in node.body:
            self.visit(statement)
        if isinstance(node.test, ast.NameConstant):
            if node.test.value is True:
                self._assembly.append(Instruction("JMP", operand=current_label))
        elif isinstance(node.test, ast.Compare):
            if len(node.test.comparators) > 1:
                assert False, "Only 1 comparator is supported for comparison"
            if len(node.test.ops) > 1:
                assert False, "Only 1 operator is supported for comparison"
            assert isinstance(node.test.ops[0], ast.Lt), "Only < is supported"

            if isinstance(node.test.comparators[0], ast.Num):
                if not 0 < node.test.comparators[0].n < 16:
                    assert False, "Only constants 0-15 are supported"
                self._assembly.append(Instruction("LDI", operand=node.test.comparators[0].n))

            if isinstance(node.test.left, ast.Name):
                assert node.test.left.id in VARS, f"{node.test.left.id} is not defined in VARS"
                var_location = VARS[node.test.left.id]
                self._assembly.append(Instruction("SUB", operand=var_location))
                end_of_loop = self.next_label()
                self._assembly.append(Instruction("LABEL", label=end_of_loop))
                self._assembly.append(Instruction("JC", operand=current_label))

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        assert node.func.id == "print", "I only know how to print()"
        assert len(node.args) == 1, "I can only print 1 item"
        if isinstance(node.args[0], ast.Name):
            assert node.args[0].id in VARS, f"Cannot find address of {node.args[0].id}"
            self._assembly.append(Instruction("DSP", operand=VARS[node.args[0].id]))
        else:
            self._assembly.append(Instruction("DSI", operand=node.args[0].n))


def main():
    # load in the script, for now just use the hard-coded script
    node = ast.parse(SCRIPT)
    compiler = Compiler()
    assembly = compiler.compile(node)
    print(assembly)


if __name__ == "__main__":
    main()
