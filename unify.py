from wtypes import *
from subst import apply_subst

def unify(t1, t2):
    # unity is ==
    if t1 == t2:
        return {}
    
    if isinstance(t1, TVar):
        return {t1.name: t2}
    
    if isinstance(t2, TVar):
        return {t2.name: t1}
    
    if isinstance(t1, TArr) and isinstance(t2, TArr):
        s1 = unify(t1.input, t2.input)
        
        new_right_1 = apply_subst(t1.output, s1)
        new_right_2 = apply_subst(t2.output, s1)
        
        s2 = unify(new_right_1, new_right_2)
        
        s1.update(s2)
        return s1

    raise Exception(f"这就没法合并了: {t1} vs {t2}")

if __name__ == "__main__":
    t_left = TArr(TVar("a"), TInt())
    t_right = TArr(TBool(), TVar("b"))
    
    try:
        solution = unify(t_left, t_right)
        print(f"{t_left} == {t_right}")
        print(f"解  : {solution}") # 应该输出 {'a': Bool, 'b': Int}
    except Exception as e:
        print(e)