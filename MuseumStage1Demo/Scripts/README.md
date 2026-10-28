# Project tools

이 스크립트들은 공유 저장소의 상대 경로를 사용합니다. 캐릭터 원본은 프로젝트 상위 `Assets/Player/night_patrol_v15/`를 참조합니다. Python 실행 파일이 필요한 도구와 언리얼 내부에서 실행해야 하는 도구를 구분합니다.

| 파일 | 용도 |
|---|---|
| `stage1_layout.py`, `gallery_floor.hlsl`, `room_floor.hlsl` | 맵 배치 및 바닥 패턴 원본 |
| `build_stage1.py` | 저장된 배치를 기준으로 맵의 생성 액터와 재질을 재구성. 수동 편집 전용 맵에는 바로 실행하지 않음 |
| `patrol_equipment.py`, `apply_patrol_equipment.py` | 장비 반입·플레이어 컴포넌트 설정·야간 조명 적용 |
| `verify_patrol_equipment.py` | 실제 PIE 키 입력·속도·점프·장비·벽 접근 검사 및 촬영 |
| `camera_collision.py`, `first_person_pawn.py` | 카메라 충돌·몸체·시점 설정 |
| `export_first_person_body.py` | Blender에서 공용 원본을 읽어 `References/FirstPersonBody/`의 파생 FBX 생성 |
| `apply_first_person_body.py`, `setup_first_person_body.py` | 언리얼에서 몸체 반입 및 템플릿 동작 리타게팅 |
| `verify_project_assets.py` | 프로젝트 전체 에셋의 끊어진 참조 검사. 언리얼 Python commandlet에서 실행 |
| `verify_first_person_assets.py`, `material_usage.py` | 저장된 캐릭터·재질 검사. 언리얼 Python commandlet에서 실행 |
| `verify_walk.py`, `verify_first_person_body.py`, `verify_camera_contacts.py` | 실제 PIE 이동·몸체·카메라 밀착 검사. commandlet 대신 에디터의 `-ExecutePythonScript`로 실행 |
| `capture_stage1.py`, `surface_review_views.py` | 실제 에디터 화면 촬영 |
| `audit_coplanar_surfaces.py` | 일반 Python에서 배치 원본의 평면 겹침 검사 |

기존 로컬 백업이나 과거 검사 파일에 의존하는 일회성 수정·패키지 정리 스크립트는 포함하지 않았습니다. 검사 결과는 Git에서 제외된 `Saved/Validation/`, 촬영 결과는 `Saved/Review/`에 생성됩니다.
