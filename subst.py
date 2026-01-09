from wtypes import *

def apply_subst(typ, subst):
    """
    Applies a substitution (a dictionary of type mappings) to a specific type.
    
    Args:
        typ: The Type object (e.g., TInt, TVar("a"), TArr...).
        subst: A dictionary mapping variable names to Types (e.g., {"a": TInt()}).
        
    Returns:
        A new Type object with the replacements applied.
    """
    if isinstance(typ, TInt):
        return typ
    elif isinstance(typ, TBool):
        return typ
    elif isinstance(typ, TVar):
        return subst.get(typ.name, typ)
    elif isinstance(typ, TArr):
        return TArr(apply_subst(typ.input, subst), 
                    apply_subst(typ.output, subst))
    elif isinstance(typ, Scheme):
        # For Scheme, avoid substituting bound variables
        # 这里vars是泛型变量
        # Example: if typ.vars = ["a"] and subst = {"a": TInt(), "b": TBool()}
        # then new_subst will be {"b": TBool()} (excluding "a" from subst)
        new_subst = {k: v for k, v in subst.items() if k not in typ.vars}
        return Scheme(typ.vars, apply_subst(typ.t, new_subst))
    # In case we have a list or dict of types to substitute

    # 暂时不知道有啥用
    elif isinstance(typ, dict):
        return {k: apply_subst(v, subst) for k, v in typ.items()}
    


def compose(s1, s2):
    """
    Example:
        s1 = {"a": TInt()}
        s2 = {"b": TVar("a"), "c": TBool()}
        # compose(s1, s2) = {"a": TInt(), "b": TInt(), "c": TBool()}
    """
    result = {k: apply_subst(v, s1) for k, v in s2.items()}
    result.update(s1)
    return result

if __name__ == "__main__":
    my_type = TArr(TVar("a"), TVar("b"))
    solution = {"a": TInt()}

    result1 = apply_subst(my_type, solution)
    result2 = apply_subst(result1, {"b": TVar("c")})

    print(f"exp: {my_type}")
    print(f"after apply_subst: {result1}") 
    print(f"after apply_subst: {result2}")

    s1 = {"a": TInt()}
    s2 = {"b": TVar("a"), "c": TBool()}
    composed = compose(s1, s2)
    print(f"s1 = {s1}")
    print(f"s2 = {s2}")
    print(f"compose(s1, s2) = {composed}")

    s3 = {"c": TVar("b")}
    s4 = {"d": TVar("c"), "e": TArr(TVar("a"), TVar("c"))}
    composed2 = compose(s3, s4)
    print(f"\ns3 = {s3}")
    print(f"s4 = {s4}")
    print(f"compose(s3, s4) = {composed2}")
    print()

    scheme = Scheme(vars=["a"], t=TArr(TVar("a"), TVar("a")))
    subst_scheme = {"a": TInt(), "b": TBool()}
    scheme_result = apply_subst(scheme, subst_scheme)
    print(f"原始 Scheme: {scheme}")       
    print(f"替换后 Scheme: {scheme_result}")  
    print()

    type_env = {"x": TVar("a"), "y": TVar("b"), "z": TArr(TVar("a"), TVar("b"))}
    env_subst = {"a": TInt(), "b": TBool()}
    new_env = apply_subst(type_env, env_subst)
    print(f"原始类型环境: {type_env}")   
    print(f"批量替换后: {new_env}")