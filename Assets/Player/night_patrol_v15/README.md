# Patrol character v15

- `night_patrol_v15_uv.blend`: 최신 편집 원본. UV·재질·뼈대와 Blender 보정 제약을 포함합니다.
- `night_patrol_v15_uv.fbx`: 언리얼 반입용 Skeletal Mesh 원본.
- `materials.json`: 8개 재질의 기본 색·거칠기·금속성 정보.
- `color_regions.json`: 피부·상의·하의·신발의 색상 영역.

기존 순찰자 v15의 최신 UV 파일을 복사했습니다. 이전 버전과 미리보기·검토 모션은 포함하지 않습니다. 기본 A포즈와 23본을 유지합니다.

Blender 보정 제약은 FBX에 그대로 전달되지 않습니다. 애니메이션을 새로 만들 때 보정 본 구동 또는 베이크 여부를 확인합니다. 현재 데모의 플레이어·리타게팅 동작은 언리얼 프로젝트의 `Content/Stage1/FirstPerson/Patrol/`에 있습니다.
