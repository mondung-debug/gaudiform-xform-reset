# -*- coding: utf-8 -*-
"""XformReset post-processing operation.

phase = "per_file" — 열린 USD stage의 defaultPrim 자식 prim 트랜스폼을
identity로 리셋하거나 완전 제거합니다.

스케줄러 config.json 예시:
    {
      "post_processing": [
        {
          "operation": "external",
          "script": "external_operations/xform_reset_operation.py",
          "params": {
            "remove_mode":  false,
            "only_names":   []
          }
        }
      ]
    }

params:
    remove_mode  (bool, default false) — true: xformOp 속성 완전 제거
                                         false: identity 값으로 리셋
    only_names   (list[str], default []) — 처리할 자식 prim 이름 목록
                                           비어 있으면 전체 자식 처리
"""

from __future__ import annotations

from gaudiform.core.post_processing import PostProcessOperation, PostProcessContext
from gaudiform.core.xform_reset.xform_reset_core import process_stage

_TAG = "XformResetOperation"


class XformResetOperation(PostProcessOperation):
    """USD defaultPrim 자식 prim 트랜스폼 초기화 오퍼레이션."""

    phase = "per_file"

    def execute(self, context: PostProcessContext) -> None:
        p = context.params
        remove_mode = bool(p.get("remove_mode", False))
        only_names = p.get("only_names") or []

        stage = context.stage
        if stage is None:
            context.on_warn(_TAG, "stage가 없습니다. 스킵합니다.")
            return

        def _info(msg: str) -> None:
            context.on_info(_TAG, msg)

        def _warn(msg: str) -> None:
            context.on_warn(_TAG, msg)

        def _log(msg: str) -> None:
            if msg.startswith("  [WARN]"):
                _warn(msg.strip())
            else:
                _info(msg.strip())

        mode_label = "제거" if remove_mode else "identity 리셋"
        filter_label = f"필터: {only_names}" if only_names else "전체 자식"
        context.on_info(_TAG, f"트랜스폼 {mode_label} 시작 — {filter_label}")

        count = process_stage(
            stage,
            remove_mode=remove_mode,
            only_names=only_names if only_names else None,
            log=_log,
        )

        context.on_info(_TAG, f"완료: {count}개 prim 처리됨")
