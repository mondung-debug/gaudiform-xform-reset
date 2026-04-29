# -*- coding: utf-8 -*-
"""
XformReset core logic — USD defaultPrim 자식 prim 트랜스폼 초기화.
pxr 단독으로 동작 (Kit/Omniverse 불필요).
"""

from __future__ import annotations

from pxr import Gf, Usd


def get_xform_ops(prim: Usd.Prim) -> list[str]:
    attr = prim.GetAttribute("xformOpOrder")
    if not attr or not attr.IsValid():
        return []
    val = attr.Get()
    return list(val) if val is not None else []


def reset_to_identity(prim: Usd.Prim, log=print) -> bool:
    """xformOp 값을 identity로 초기화. 변경이 없으면 False 반환."""
    ops = get_xform_ops(prim)
    if not ops:
        return False
    for op_name in ops:
        if op_name.startswith("!resetXformStack!"):
            continue
        attr = prim.GetAttribute(op_name)
        if not attr or not attr.IsValid():
            continue
        name_lower = op_name.lower()
        try:
            if "translate" in name_lower:
                attr.Set(Gf.Vec3d(0, 0, 0))
            elif "scale" in name_lower:
                attr.Set(Gf.Vec3f(1, 1, 1))
            elif "orient" in name_lower:
                attr.Set(Gf.Quatf(1, 0, 0, 0))
            elif "rotate" in name_lower:
                try:    attr.Set(Gf.Vec3f(0, 0, 0))
                except: attr.Set(Gf.Vec3d(0, 0, 0))
            elif "matrix" in name_lower or "transform" in name_lower:
                attr.Set(Gf.Matrix4d(1))
            else:
                attr.Set(Gf.Vec3d(0, 0, 0))
        except Exception as e:
            log(f"  [WARN] {op_name} 리셋 실패: {e}")
    log(f"  [RESET] {prim.GetPath()} — {len(ops)} op(s) → identity")
    return True


def remove_xform_ops(prim: Usd.Prim, log=print) -> bool:
    """xformOp 속성과 xformOpOrder를 완전 제거."""
    ops = get_xform_ops(prim)
    removed = 0
    for op_name in ops:
        if op_name.startswith("!resetXformStack!"):
            continue
        attr = prim.GetAttribute(op_name)
        if attr and attr.IsValid():
            prim.RemoveProperty(op_name)
            removed += 1
    order_attr = prim.GetAttribute("xformOpOrder")
    if order_attr and order_attr.IsValid():
        prim.RemoveProperty("xformOpOrder")
    if removed > 0 or ops:
        log(f"  [REMOVE] {prim.GetPath()} — {removed} op(s) 제거")
        return True
    return False


def process_stage(
    stage: Usd.Stage,
    remove_mode: bool = False,
    only_names: list[str] | None = None,
    log=print,
) -> int:
    """
    stage의 defaultPrim 바로 아래 자식 prim 트랜스폼 처리.

    Args:
        stage:       처리할 Usd.Stage
        remove_mode: True → xformOp 완전 제거 / False → identity 리셋
        only_names:  처리할 자식 prim 이름 목록 (None 또는 빈 리스트 = 전체)
        log:         로그 콜백

    Returns:
        처리된 prim 수
    """
    default_prim = stage.GetDefaultPrim()
    if not default_prim or not default_prim.IsValid():
        log("[WARN] defaultPrim 없음")
        return 0

    processed = 0
    for child in default_prim.GetChildren():
        if only_names and child.GetName() not in only_names:
            continue
        fn = remove_xform_ops if remove_mode else reset_to_identity
        if fn(child, log=log):
            processed += 1

    return processed
