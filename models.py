from dataclasses import dataclass

class DISJUNCT:
    def __init__(self, literals=None):
        self.literals = literals if literals is not None else []
    def __repr__(self) -> str:
        return f"DISJUNCT(\n\t{"\n\t".join(repr(lit) for lit in self.literals)} \n)"
    def __str__(self):
        return "\n".join(str(lit) for lit in self.literals)

@dataclass
class CONSTANT:
    name: str
    def __repr__(self) -> str:
        return f"CONST({self.name})"
    def __str__(self) -> str:
        return self.name

@dataclass
class VAR:
    name: str
    is_free: bool = False
    def __repr__(self) -> str:
        return f"VAR({self.name},{'free' if self.is_free else 'bound'})"
    def __str__(self) -> str:
        return self.name

@dataclass
class ATOMICITY:
    var: VAR
    def __repr__(self) -> str:
        return f"ATOMICITY({self.var})"
    def __str__(self) -> str:
        return f"At({self.var})"

@dataclass
class CONSTRUCTOR_TERM:
    constr: str
    var_list: list

    def __repr__(self) -> str:
        return f"CONSTR_TERM({self.constr}({self.var_list}))"
    def __str__(self) -> str:
        return f"{self.constr}({','.join([str(v) for v in self.var_list])})"

@dataclass
class EQUALITY:
    lhs: VAR
    rhs: VAR | CONSTRUCTOR_TERM | CONSTANT
    def __repr__(self) -> str:
        return f"EQUALITY({repr(self.lhs)} = {repr(self.rhs)})"
    def __str__(self) -> str:
        return f"{self.lhs} = {self.rhs}"

@dataclass
class INEQUALITY:
    lhs: VAR
    rhs: VAR | CONSTANT

    def __repr__(self) -> str:
        return f"INEQ({self.lhs} != {self.rhs})"
    def __str__(self) -> str:
        return f"{self.lhs} != {self.rhs}"