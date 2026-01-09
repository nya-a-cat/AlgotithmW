from dataclasses import dataclass

class Type: pass

@dataclass
class TInt(Type):
    def __repr__(self): return "ourInt"

@dataclass
class TBool(Type):
    def __repr__(self): return "ourBool"

@dataclass
class TVar(Type):
    name: str
    def __repr__(self): return self.name  # ti

@dataclass
class TArr(Type):
    input: Type
    output: Type
    def __repr__(self): return f"({self.input} -> {self.output})"

@dataclass
class Scheme(Type):
    vars: list[str] # 泛型变量列表
    t: Type
    def __repr__(self): return f"(forall){','.join(self.vars)}. {self.t}"

@dataclass
class TArray(Type):
    element_type: Type
    def __repr__(self): return f"Array[{self.element_type}]"

@dataclass
class TRecord(Type):
    fields: dict[str, Type]
    def __repr__(self):
        field_str = ', '.join(f"{k}: {v}" for k, v in self.fields.items())
        return f"{{{field_str}}}"

# find free type variables
def ftv(t) -> set:
    if isinstance(t, TInt) or isinstance(t, TBool):
        return set()
    if isinstance(t, TVar):
        return {t.name}
    if isinstance(t, TArr):
        return ftv(t.input) | ftv(t.output)
    if isinstance(t, Scheme):
        return ftv(t.t) - set(t.vars)
    if isinstance(t, TArray):
        return ftv(t.element_type)
    if isinstance(t, TRecord):
        return set().union(*[ftv(v) for v in t.fields.values()]) if t.fields else set()
    if isinstance(t, list): # 处理列表
        return set().union(*[ftv(x) for x in t])
    if isinstance(t, dict): # 处理环境 env
        return set().union(*[ftv(x) for x in t.values()])
    return set()


if __name__ == "__main__":
    t1 = TInt()
    t2 = TVar("a")
    t3 = TArr(t1, t2) # Int -> a
    t4 = TArr(t3, TBool()) # (Int -> a) -> Bool

    print(f"类型1: {t1}")
    print(f"类型2: {t2}")
    print(f"类型3: {t3}")
    print(f"类型4: {t4}")

    print(f"FTV of {t4}: {ftv(t4)}") 

    t_nested = TArr(
        TArr(TVar("a"), TInt()), 
        TArr(TVar("b"), TArr(TVar("a"), TVar("c")))
    )
    print(f"类型: {t_nested}")
    # 逻辑: Union({a}, {}) | Union({b}, {a, c}) => {a, b, c}
    print(f"FTV: {ftv(t_nested)}") 

    t_poly1 = Scheme(["a"], TArr(TVar("a"), TVar("b")))
    print(f"Scheme A: {t_poly1}")
    print(f"FTV: {ftv(t_poly1)}")