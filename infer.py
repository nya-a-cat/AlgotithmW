from wtypes import *
from subst import apply_subst, compose, ftv
from unify import unify
from wast import *

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

    def infer(self, env, expr):
        match expr:
            case EInt():
                return {}, TInt()

            case EBool():
                return {}, TBool()

            case EVar(name):
                if name not in env:
                    raise Exception(f"未定义的变量: {name}")
                t = env[name]
                # 如果是 Scheme (∀)，则实例化
                if isinstance(t, Scheme):
                    return {}, self.instantiate(t)
                return {}, t

            case EAbs(arg, body):
                arg_type = self.new_tvar()
                new_env = {**env, arg: arg_type}
                s, body_type = self.infer(new_env, body)
                return s, TArr(apply_subst(arg_type, s), body_type)

            case EApp(func, arg):
                s1, t_func = self.infer(env, func)
                s2, t_arg = self.infer(apply_subst(env, s1), arg)
                
                t_res = self.new_tvar()
                s3 = unify(apply_subst(t_func, s2), TArr(t_arg, t_res))
                
                final_s = compose(s3, compose(s2, s1))
                return final_s, apply_subst(t_res, s3)

            case ELet(name, value, body):
                pass

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
        ("Identity", EAbs("x", EVar("x"))),
        ("Record test", ERecord({"id": EInt(1), "ok": EBool(True)})),
        ("Let Poly", ELet("id", EAbs("x", EVar("x")), 
                          EApp(EVar("id"), EInt(42)))),
    ]

    for desc, code in tests:
        try:
            s, t = ctx.infer({}, code)
            print(f"{desc:12} => {t}")
        except Exception as e:
            print(f"{desc:12} => Error: {e}")