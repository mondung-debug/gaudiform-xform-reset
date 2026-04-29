# gaudiform-xform-reset

USD defaultPrim 자식 prim 트랜스폼 초기화 — gaudiform 익스터널 스크립트 모듈

## 구조

```
gaudiform/
  core/
    xform_reset/
      xform_reset_core.py       — 핵심 로직 (pxr 단독 동작)
      xform_reset_operation.py  — PostProcessOperation 구현 (gaudiform 스케줄러 연동)
      __init__.py
    __init__.py
  __init__.py
```

## 통합 방법

1. 이 저장소를 프로젝트에 복사하거나 `sys.path`에 추가합니다.
2. gaudiform 스케줄러 `config.json`의 `post_processing` 항목에 등록합니다.

---

## 스케줄러 파라미터

```json
{
  "post_processing": [
    {
      "operation": "external",
      "script": "gaudiform/core/xform_reset/xform_reset_operation.py",
      "params": {
        "remove_mode": false,
        "only_names":  []
      }
    }
  ]
}
```

### 파라미터 상세

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `remove_mode` | `false` | `false`: xformOp 값을 identity로 리셋 / `true`: xformOp 속성 완전 제거 |
| `only_names` | `[]` | 처리할 자식 prim 이름 목록. 비어 있으면 전체 자식 처리 |

### 동작 방식

- **`remove_mode: false`** (기본): `translate → (0,0,0)`, `scale → (1,1,1)`, `orient → identity quat`, `rotate → (0,0,0)`, `matrix → identity`
- **`remove_mode: true`**: xformOp 속성과 `xformOpOrder`를 완전 삭제
- `only_names`가 지정된 경우 해당 이름의 자식 prim만 처리

### 예시

특정 prim만 리셋:
```json
{
  "remove_mode": false,
  "only_names": ["Chassis", "Body", "Wheel_FL"]
}
```

전체 자식 xformOp 완전 제거:
```json
{
  "remove_mode": true,
  "only_names": []
}
```
