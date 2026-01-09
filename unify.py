from wtypes import *
from subst import apply_subst

def occur_check(var_name, typ):
    """检查类型变量是否出现在类型中（防止无限类型）"""
    return var_name in ftv(typ)

def unify(t1, t2):
    # unity is ==
    if t1 == t2:
        return {}
    
    if isinstance(t1, TVar):
        if occur_check(t1.name, t2):
            raise Exception(f"occur check 失败: {t1.name} 出现在 {t2} 中")
        return {t1.name: t2}
    
    if isinstance(t2, TVar):
        if occur_check(t2.name, t1):
            raise Exception(f"occur check 失败: {t2.name} 出现在 {t1} 中")
        return {t2.name: t1}
    
    if isinstance(t1, TArr) and isinstance(t2, TArr):
        s1 = unify(t1.input, t2.input)
        
        new_right_1 = apply_subst(t1.output, s1)
        new_right_2 = apply_subst(t2.output, s1)
        
        s2 = unify(new_right_1, new_right_2)
        
        s1.update(s2)
        return s1
    
    if isinstance(t1, TArray) and isinstance(t2, TArray):
        return unify(t1.element_type, t2.element_type)
    
    if isinstance(t1, TRecord) and isinstance(t2, TRecord):
        if set(t1.fields.keys()) != set(t2.fields.keys()):
            raise Exception(f"记录字段不匹配: {set(t1.fields.keys())} vs {set(t2.fields.keys())}")
        
        subst = {}
        for key in t1.fields:
            s = unify(apply_subst(t1.fields[key], subst), 
                     apply_subst(t2.fields[key], subst))
            subst.update(s)
        return subst

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