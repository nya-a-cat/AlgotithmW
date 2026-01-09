module Main (Exp (..),
Type(..),
ti, -- ti::TypeEnv->Exp->(Subst,Type)
main
) where

import qualified Data.Map as Map
import qualified Data.Set as Set

import Control.Monad.Except
import Control.Monad.Reader
import Control.Monad.State

import qualified Text.PrettyPrint as PP

data Exp = EVar String
    | ELit Lit
    | EApp Exp Exp
    | EAbs String Exp
    | ELet String Exp Exp
    deriving (Eq, Ord, Show)

data Lit = LInt Integer
    | LBool Bool
    deriving (Eq, Ord, Show)

data Type = TVar String
    | TInt
    | TBool
    | TFun Type Type
    deriving (Eq, Ord, Show)

data Scheme = Scheme [String] Type
    deriving (Eq, Show)

-- fuction ftv implements to determine the free variables of a type 
-- we imp type in class Types cuz for some env reason
class Types a where
  ftv :: a -> Set.Set String
  apply :: Subst -> a -> a

instance Types Type where
  ftv (TVar n) = Set.singleton n
  ftv TInt = Set.empty
  ftv TBool = Set.empty
  ftv (TFun t1 t2) = ftv t1 `Set.union` ftv t2

  apply s (TVar n) = case Map.lookup n s of
      Just t -> t
      Nothing -> TVar n

  apply s (TFun t1 t2) = TFun (apply s t1) (apply s t2)
  apply s t = t

instance Types Scheme where
  ftv (Scheme vars t) = ftv t `Set.difference` Set.fromList vars
  --   we call \ remove
  apply s (Scheme vars t) = Scheme vars (apply s' t)
      where s' = foldr Map.delete s vars

instance Types a => Types [a] where
    apply s = map (apply s)
    ftv l = Set.unions (map ftv l)
-- define substitutions which map type variables to types
type Subst = Map.Map String Type
nullSubst :: Subst
nullSubst = Map.empty
composeSubst :: Subst -> Subst -> Subst
composeSubst s1 s2 = Map.map (apply s1) s2 `Map.union` s1

newtype TypeEnv = TypeEnv (Map.Map String Scheme)
remove :: TypeEnv -> String -> TypeEnv
remove (TypeEnv env) var = TypeEnv (Map.delete var env)
extend :: TypeEnv -> (String, Scheme) -> TypeEnv
extend (TypeEnv env) (var, scheme) = TypeEnv (Map.insert var scheme env)
instance Types TypeEnv where
    ftv (TypeEnv env) = ftv (Map.elems env)
    apply s (TypeEnv env) = TypeEnv (Map.map (apply s) env)

-- type are free? no free?what is free?
-- gene a type over typevaria bles not free in the type environment
generalize :: TypeEnv -> Type -> Scheme
generalize env t = Scheme vars t
    where vars = Set.toList (ftv t `Set.difference` ftv env)

data TIEnv = Tienv
type TIstate = Integer
type TI a = 
    ExceptT String (ReaderT TIEnv (State TIstate)) a
runTI :: TI a -> Either String a

runTI t = fst $ runState (runReaderT (runExceptT t) Tienv) 0

newTyVar :: TI Type
newTyVar = do
    s <- get
    put (s + 1)
    return (TVar (toTyVar s))
  where
    toTyVar :: Integer -> String
    toTyVar c | c < 26 = [toEnum (97 + fromIntegral c)]
              | otherwise = let (n, r) = c `divMod` 26 in toTyVar (n - 1) ++ [toEnum (97 + fromIntegral r)]

instantiate :: Scheme -> TI Type
instantiate (Scheme vars t) = do 
    nvars <- mapM (const newTyVar) vars
    let s = Map.fromList (zip vars nvars)
    return (apply s t)

-- mgu (Most General Unifier) 的作用是寻找一个最一般推导（代换），
-- 使得在该代换下两个类型表达式相等。
-- 一个代换 s 是 t1 和 t2 的统一项 (unifier)，如果 apply s t1 == apply s t2。
-- mgu 是所有统一项中最具代表性的一个。
mgu :: Type -> Type -> TI Subst
mgu (TFun l r) (TFun l' r') = do
    s1 <- mgu l l'
    s2 <- mgu (apply s1 r) (apply s1 r')
    return (s2 `composeSubst` s1)
-- 处理类型变量的统一
mgu (TVar u) t = varBind u t
mgu t (TVar u) = varBind u t
-- 处理基本类型的统一
mgu TInt TInt = return nullSubst
mgu TBool TBool = return nullSubst
-- 无法统一时抛出错误
mgu t1 t2 = throwError $ "types do not unify: " ++ show t1 ++ " vs. " ++ show t2

varBind :: String -> Type -> TI Subst
varBind u t
    | t == TVar u = return nullSubst
    | u `Set.member` ftv t = throwError $ "occur check fails: " ++ u ++ " vs. " ++ show t
    | otherwise = return (Map.singleton u t)
-- tolit

tiLit :: Lit -> TI (Subst, Type)
tiLit (LInt _) = return (nullSubst, TInt)
tiLit (LBool _) = return (nullSubst, TBool)

-- ti infer the types for e
-- must contain bindings for all free variable of the expression
ti :: TypeEnv -> Exp -> TI (Subst, Type)
ti (TypeEnv env) (EVar n) =
    case Map.lookup n env of
        Nothing -> throwError $ "unbound variable: " ++ n
        Just sigma -> do
            t <- instantiate sigma
            return (nullSubst, t)
ti env (ELit l) = tiLit l
ti env (EAbs n e) = do
    tv <- newTyVar
    let TypeEnv env' = remove env n
        env'' = TypeEnv (env' `Map.union` Map.singleton n (Scheme [] tv))
    (s1, t1) <- ti env'' e
    return (s1, TFun (apply s1 tv) t1)

ti env (EApp e1 e2) = do
    tv <- newTyVar
    (s1, t1) <- ti env e1
    (s2, t2) <- ti (apply s1 env) e2
    s3 <- mgu (apply s2 t1) (TFun t2 tv)
    return (s3 `composeSubst` s2 `composeSubst` s1, apply s3 tv)
ti env (ELet x e1 e2) = do
    (s1, t1) <- ti env e1
    let env' = apply s1 env
        t' = generalize env' t1
        env'' = extend env' (x, t')
    (s2, t2) <- ti env'' e2
    return (s2 `composeSubst` s1, t2)

typeInference :: Map.Map String Scheme -> Exp -> TI Type
typeInference env e = do
    (s, t) <- ti (TypeEnv env) e
    return (apply s t)

e0 = ELet "id" (EAbs "x" (EVar "x"))
         (EApp (EVar "id") (ELit (LInt 42)))

e1 = ELet "id" (EAbs "x" (EVar "x"))
         (EApp (EVar "id") (ELit (LBool True)))

e2 = EAbs "x" (EVar "x")

e3 = EApp (EAbs "x" (EVar "x")) (ELit (LInt 5))

e4 = ELit (LInt 42)

e5 = ELit (LBool False)

test :: Exp -> IO ()
test e = 
    let res = runTI (typeInference Map.empty e) in
    case res of
        Left err -> putStrLn $ "Error: " ++ err
        Right t  -> putStrLn $ "Type: " ++ show t

main :: IO ()
main = do
    putStrLn "Testing type inference:"
    mapM_ test [e0, e1, e2, e3, e4, e5]