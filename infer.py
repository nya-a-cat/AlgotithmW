from wtypes import *
from subst import apply_subst, compose, ftv
from unify import unify
from wast import *
from pprint import pprint

def pretty_expr(expr):
    """美化表达式输出"""
    match expr:
        case EInt(n):
            return str(n)
        case EBool(b):
            return str(b)
        case EVar(name):
            return name
        case EAbs(arg, body):
            return f"λ{arg}.{pretty_expr(body)}"
        case EApp(func, arg):
            func_str = pretty_expr(func)
            arg_str = pretty_expr(arg)
            if isinstance(arg, (EAbs, ELet)):
                arg_str = f"({arg_str})"
            return f"{func_str} {arg_str}"
        case ELet(name, value, body):
            return f"let {name} = {pretty_expr(value)} in {pretty_expr(body)}"
        case EArray(elements):
            return f"[{', '.join(pretty_expr(e) for e in elements)}]"
        case ERecord(fields):
            items = ', '.join(f"{k}: {pretty_expr(v)}" for k, v in fields.items())
            return f"{{{items}}}"
        case _:
            return str(expr)

class InferContext:
    def __init__(self):
        self.counter = 0

    def new_tvar(self):
        t = TVar(f"t{self.counter}")
        self.counter += 1
        return t

    def instantiate(self, scheme: Scheme):
        # 把 ∀a, b. T 里的 a, b 换成全新的 t1, t2
        subst = {v: self.new_tvar() for v in scheme.vars}
        return apply_subst(scheme.t, subst)

    def generalize(self, env, t):
        # 找出 t 中存在但 env 中不存在的自由变量进行泛化
        gen_vars = list(ftv(t) - ftv(env))
        return Scheme(gen_vars, t) if gen_vars else t

    def infer(self, env, expr, debug=False, depth=0):
        indent = "  " * depth
        
        if debug:
            print(f"{indent}推导: {pretty_expr(expr)}")
            if env:
                print(f"{indent}环境: {{{', '.join(f'{k}: {v}' for k, v in env.items())}}}")
        
        match expr:
            case EInt():
                if debug:
                    print(f"{indent}=> Int\n")
                return {}, TInt()

            case EBool():
                if debug:
                    print(f"{indent}=> Bool\n")
                return {}, TBool()

            case EVar(name):
                if name not in env:
                    raise Exception(f"未定义的变量: {name}")
                t = env[name]
                # 如果是 Scheme (∀)，则实例化
                if isinstance(t, Scheme):
                    inst = self.instantiate(t)
                    if debug:
                        print(f"{indent}实例化 {t} => {inst}")
                        print(f"{indent}=> {inst}\n")
                    return {}, inst
                if debug:
                    print(f"{indent}=> {t}\n")
                return {}, t

            case EAbs(arg, body):
                arg_type = self.new_tvar()
                if debug:
                    print(f"{indent}参数 {arg} : {arg_type}")
                new_env = {**env, arg: arg_type}
                s, body_type = self.infer(new_env, body, debug, depth+1)
                result = TArr(apply_subst(arg_type, s), body_type)
                if debug:
                    if s:
                        print(f"{indent}替换: {dict(s)}")
                    print(f"{indent}=> {result}\n")
                return s, result

            case EApp(func, arg):
                if debug:
                    print(f"{indent}[函数部分]")
                s1, t_func = self.infer(env, func, debug, depth+1)
                if debug:
                    print(f"{indent}[参数部分]")
                s2, t_arg = self.infer(apply_subst(env, s1), arg, debug, depth+1)
                
                t_res = self.new_tvar()
                if debug:
                    print(f"{indent}统一: {apply_subst(t_func, s2)} = {t_arg} -> {t_res}")
                s3 = unify(apply_subst(t_func, s2), TArr(t_arg, t_res))
                
                final_s = compose(s3, compose(s2, s1))
                result = apply_subst(t_res, s3)
                if debug:
                    if s3:
                        print(f"{indent}统一替换: {dict(s3)}")
                    print(f"{indent}=> {result}\n")
                return final_s, result

            case ELet(name, value, body):
                # 推导e1表达式类型
                if debug:
                    print(f"{indent}[推导绑定值]")
                s1, t1 = self.infer(env, value, debug, depth+1)
                # 替换
                env1 = apply_subst(env, s1)
                # 泛化类型
                scheme = self.generalize(env1, t1)
                if debug:
                    print(f"{indent}泛化: {name} : {scheme}")
                    print(f"{indent}[推导body]")
                # 新环境推导e2
                env2 = env1.copy()
                env2[name] = scheme
                s2, t2 = self.infer(env2, body, debug, depth+1)
                # 组合替换返回结果
                if debug:
                    print(f"{indent}=> {t2}\n")
                return compose(s2, s1), t2

            case EArray(elements):
                if not elements:
                    return {}, TArray(self.new_tvar())
                
                s_accum, t_elem = self.infer(env, elements[0])
                for elem in elements[1:]:
                    s_next, t_next = self.infer(apply_subst(env, s_accum), elem)
                    s_u = unify(apply_subst(t_elem, s_next), t_next)
                    s_accum = compose(s_u, compose(s_next, s_accum))
                    t_elem = apply_subst(t_elem, s_u)
                return s_accum, TArray(t_elem)

            case ERecord(fields):
                res_fields = {}
                s_accum = {}
                for name, field_expr in fields.items():
                    s_item, t_item = self.infer(apply_subst(env, s_accum), field_expr)
                    s_accum = compose(s_item, s_accum)
                    res_fields[name] = t_item
                
                final_fields = {k: apply_subst(v, s_accum) for k, v in res_fields.items()}
                return s_accum, TRecord(final_fields)

            case _:
                raise Exception(f"Unknown expression type: {type(expr)}")

if __name__ == "__main__":
    ctx = InferContext()
    tests = [
        # 基础测试
        ("Identity", EAbs("x", EVar("x"))),
        ("Record test", ERecord({"id": EInt(1), "ok": EBool(True)})),
        ("Let Poly", ELet("id", EAbs("x", EVar("x")), 
                          EApp(EVar("id"), EInt(42)))),
        
        # 嵌套 let: let x = 5 in let y = True in {x, y}
        ("Nested let", ELet("x", EInt(5),
                           ELet("y", EBool(True),
                               ERecord({"x": EVar("x"), "y": EVar("y")})))),
        
        # 一个始终返回第二个参数的函数 (fun x -> let y = fun z -> z in y) 1 2 ==> 2
        # 恭喜我这个测试结果是对的，虽然我看不懂
        ("Level test", EAbs("x", ELet("y", EAbs("z", EVar("z")), EVar("y")))),

        # 群友给的经典例子
        # fun x -> let y = x in y
        ("Alias let", EAbs("x", ELet("y", EVar("x"), EVar("y")))),
        # fun x -> let y = fun z -> x z in y
        ("Apply-through let", EAbs("x", ELet("y", EAbs("z", EApp(EVar("x"), EVar("z"))), EVar("y")))),
    ]
    

    print("\n" + "="*80)
    print("Algorithm W 类型推导测试")
    print("="*80)
    
    # 设置为 True 查看详细推导过程
    SHOW_DETAIL = True
    
    for i, (desc, code) in enumerate(tests, 1):
        print(f"\n[测试 {i}] {desc}")
        print(f"表达式: {pretty_expr(code)}")
        
        if SHOW_DETAIL:
            print("\n推导过程:")
            print("-"*20)
        
        try:
            ctx_test = InferContext()
            s, t = ctx_test.infer({}, code, debug=SHOW_DETAIL)
            
            if SHOW_DETAIL:
                print("-"*20)
            
            print(f"\n✓ 类型: {t}")
            if s and len(s) > 0:
                print(f"\n替换集:")
                for var in sorted(s.keys()):
                    print(f"  {var} ↦ {s[var]}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")
        
        print("\n" + "="*20)