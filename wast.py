from dataclasses import dataclass

class Expr: pass

@dataclass
class EInt(Expr):
    val: int  

@dataclass
class EVar(Expr):
    name: str 

@dataclass
class EBool(Expr):
    val: bool 

@dataclass
class EApp(Expr): 
    func: Expr
    arg: Expr

@dataclass
class EAbs(Expr): 
    arg: str  
    body: Expr

@dataclass
class EArray(Expr):
    elements: list[Expr]
    def __repr__(self):
        inner = ", ".join(repr(e) for e in self.elements)
        return f"[{inner}]"

@dataclass
class ERecord(Expr):
    fields: dict[str, Expr]
    def __repr__(self):
        field_str = ', '.join(f"{k}: {repr(v)}" for k, v in self.fields.items())
        return f"{{{field_str}}}"

# 多态
@dataclass
class ELet(Expr):
    name: str
    val: Expr  # let x = val
    body: Expr # in body

if __name__ == "__main__":
    code = EApp(EAbs("x", EVar("x")), EInt(10))
    print(code)