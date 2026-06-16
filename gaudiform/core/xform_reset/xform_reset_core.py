# -*- coding: utf-8 -*-
"""
XformReset core logic — USD defaultPrim 자식 prim 트랜스폼 초기화.
pxr 단독으로 동작 (Kit/Omniverse 불필요).
"""

from __future__ import annotations

from pxr import Gf, Sdf, Usd

_BACKUP_NS = "xformResetBackup"


def get_xform_ops(prim: Usd.Prim) -> list[str]:
    attr = prim.GetAttribute("xformOpOrder")
    if not attr or not attr.IsValid():
        return []
    val = attr.Get()
    return list(val) if val is not None else []


def _backup_key(op_name: str) -> str:
    """xformOp:translate → xformResetBackup:translate"""
    short = op_name.split(":", 1)[-1] if ":" in op_name else op_name
    return f"{_BACKUP_NS}:{short}"


def save_xform_backup(prim: Usd.Prim, log=print) -> None:
    """리셋 전 xformOp 값을 xformResetBackup:* 커스텀 속성으로 저장."""
    ops = get_xform_ops(prim)
    if not ops:
        return

    # opOrder 백업
    order_key = f"{_BACKUP_NS}:opOrder"
    order_attr = prim.GetAttribute(order_key)
    if not order_attr or not order_attr.IsValid():
        order_attr = prim.CreateAttribute(order_key, Sdf.ValueTypeNames.TokenArray, custom=True)
    order_attr.Set(ops)

    for op_name in ops:
        if op_name.startswith("!resetXformStack!"):
            continue
        src = prim.GetAttribute(op_name)
        if not src or not src.IsValid():
            continue
        val = src.Get()
        if val is None:
            continue
        bk_name = _backup_key(op_name)
        bk = prim.GetAttribute(bk_name)
        if not bk or not bk.IsValid():
            bk = prim.CreateAttribute(bk_name, src.GetTypeName(), custom=True)
        try:
            bk.Set(val)
        except Exception as e:
            log(f"  [WARN] 백업 실패 {op_name}: {e}")

    log(f"  [BACKUP] {prim.GetPath()} — {len(ops)} op(s) 저장")


def reset_to_identity(prim: Usd.Prim, log=print, save_backup: bool = True) -> bool:
    """xformOp 값을 identity로 초기화. 변경이 없으면 False 반환."""
    ops = get_xform_ops(prim)
    if not ops:
        return False
    if save_backup:
        save_xform_backup(prim, log=log)
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
    save_backup: bool = True,
    log=print,
) -> int:
    """
    stage의 defaultPrim 바로 아래 자식 prim 트랜스폼 처리.

    Args:
        stage:       처리할 Usd.Stage
        remove_mode: True → xformOp 완전 제거 / False → identity 리셋
        only_names:  처리할 자식 prim 이름 목록 (None 또는 빈 리스트 = 전체)
        save_backup: True → 리셋 전 원본값을 xformResetBackup:* 속성으로 저장
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
        if remove_mode:
            if remove_xform_ops(child, log=log):
                processed += 1
        else:
            if reset_to_identity(child, log=log, save_backup=save_backup):
                processed += 1

    return processed
