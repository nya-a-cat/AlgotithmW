## 参考资料

- [Algorithm W Step by Step](https://github.com/wh5a/Algorithm-W-Step-By-Step)

## 测试输出

```
================================================================================
Algorithm W 类型推导测试
================================================================================

[测试 1] Identity
表达式: λx.x

推导过程:
--------------------
推导: λx.x
参数 x : t0
  推导: x
  环境: {x: t0}
  => t0

=> (t0 -> t0)

--------------------

✓ 类型: (t0 -> t0)

====================

[测试 2] Record test
表达式: {id: 1, ok: True}

推导过程:
--------------------
推导: {id: 1, ok: True}
[记录字段推导] 共 2 项
字段 id:
  推导: 1
  => Int

字段 ok:
  推导: True
  => Bool

=> {id: ourInt, ok: ourBool}

--------------------

✓ 类型: {id: ourInt, ok: ourBool}

====================

[测试 3] Let Poly
表达式: let id = λx.x in id 42

推导过程:
--------------------
推导: let id = λx.x in id 42
[推导绑定值]
  推导: λx.x
  参数 x : t0
    推导: x
    环境: {x: t0}
    => t0

  => (t0 -> t0)

泛化: id : (forall)t0. (t0 -> t0)
[推导body]
  推导: id 42
  环境: {id: (forall)t0. (t0 -> t0)}
  [函数部分]
    推导: id
    环境: {id: (forall)t0. (t0 -> t0)}
    实例化 (forall)t0. (t0 -> t0) => (t1 -> t1)
    => (t1 -> t1)

  [参数部分]
    推导: 42
    环境: {id: (forall)t0. (t0 -> t0)}
    => Int

  统一: (t1 -> t1) = ourInt -> t2
  统一替换: {'t1': ourInt, 't2': ourInt}
  => ourInt

=> ourInt

--------------------

✓ 类型: ourInt

替换集:
  t1 ↦ ourInt
  t2 ↦ ourInt

====================

[测试 4] Nested let
表达式: let x = 5 in let y = True in {x: x, y: y}

推导过程:
--------------------
推导: let x = 5 in let y = True in {x: x, y: y}
[推导绑定值]
  推导: 5
  => Int

泛化: x : ourInt
[推导body]
  推导: let y = True in {x: x, y: y}
  环境: {x: ourInt}
  [推导绑定值]
    推导: True
    环境: {x: ourInt}
    => Bool

  泛化: y : ourBool
  [推导body]
    推导: {x: x, y: y}
    环境: {x: ourInt, y: ourBool}
    [记录字段推导] 共 2 项
    字段 x:
      推导: x
      环境: {x: ourInt, y: ourBool}
      => ourInt

    字段 y:
      推导: y
      环境: {x: ourInt, y: ourBool}
      => ourBool

    => {x: ourInt, y: ourBool}

  => {x: ourInt, y: ourBool}

=> {x: ourInt, y: ourBool}

--------------------

✓ 类型: {x: ourInt, y: ourBool}

====================

[测试 5] Level test
表达式: λx.let y = λz.z in y

推导过程:
--------------------
推导: λx.let y = λz.z in y
参数 x : t0
  推导: let y = λz.z in y
  环境: {x: t0}
  [推导绑定值]
    推导: λz.z
    环境: {x: t0}
    参数 z : t1
      推导: z
      环境: {x: t0, z: t1}
      => t1

    => (t1 -> t1)

  泛化: y : (forall)t1. (t1 -> t1)
  [推导body]
    推导: y
    环境: {x: t0, y: (forall)t1. (t1 -> t1)}
    实例化 (forall)t1. (t1 -> t1) => (t2 -> t2)
    => (t2 -> t2)

  => (t2 -> t2)

=> (t0 -> (t2 -> t2))

--------------------

✓ 类型: (t0 -> (t2 -> t2))

====================

[测试 6] Alias let
表达式: λx.let y = x in y

推导过程:
--------------------
推导: λx.let y = x in y
参数 x : t0
  推导: let y = x in y
  环境: {x: t0}
  [推导绑定值]
    推导: x
    环境: {x: t0}
    => t0

  泛化: y : t0
  [推导body]
    推导: y
    环境: {x: t0, y: t0}
    => t0

  => t0

=> (t0 -> t0)

--------------------

✓ 类型: (t0 -> t0)

====================

[测试 7] Apply-through let
表达式: λx.let y = λz.x z in y

推导过程:
--------------------
推导: λx.let y = λz.x z in y
参数 x : t0
  推导: let y = λz.x z in y
  环境: {x: t0}
  [推导绑定值]
    推导: λz.x z
    环境: {x: t0}
    参数 z : t1
      推导: x z
      环境: {x: t0, z: t1}
      [函数部分]
        推导: x
        环境: {x: t0, z: t1}
        => t0

      [参数部分]
        推导: z
        环境: {x: t0, z: t1}
        => t1

      统一: t0 = t1 -> t2
      统一替换: {'t0': (t1 -> t2)}
      => t2

    替换: {'t0': (t1 -> t2)}
    => (t1 -> t2)

  泛化: y : (t1 -> t2)
  [推导body]
    推导: y
    环境: {x: (t1 -> t2), y: (t1 -> t2)}
    => (t1 -> t2)

  => (t1 -> t2)

替换: {'t0': (t1 -> t2)}
=> ((t1 -> t2) -> (t1 -> t2))

--------------------

✓ 类型: ((t1 -> t2) -> (t1 -> t2))

替换集:
  t0 ↦ (t1 -> t2)

====================
```
