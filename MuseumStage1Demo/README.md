# MuseumStage1Demo

Unreal Engine **5.7.4**용 1스테이지 1인칭 이동 데모입니다.

빌드 준비와 조작키는 [저장소 안내](../README.md#처음-실행)를 참고합니다. `MuseumStage1Demo.uproject`를 열고 Play를 누릅니다. `Open_Editor.cmd`와 `Run_FirstPerson.cmd`는 기본 설치 경로 `C:\Program Files\Epic Games\UE_5.7`을 사용하므로 엔진 설치 위치가 다르면 스크립트의 `UE_EDITOR`를 수정합니다.

맵은 `Content/Stage1/Maps/L_MuseumStage1.umap`입니다. 2층 박물관 구조·전시실·관계자 복도·야간 조명과 순찰자 더미, 1인칭 몸체·이동 동작, 달리기, 손전등·노트 전환을 포함합니다. 현재 데모는 1인 이동 확인용이며 협동·유물 AI·봉인 퍼즐 기능은 후속 작업입니다.

최신 캐릭터 원본은 저장소의 `../Assets/Player/night_patrol_v15/`에 있습니다. `References/FirstPersonBody/`는 해당 모델에서 파생된 전신·1인칭용 FBX입니다.

공유 규칙은 [저장소 안내](../README.md)와 [협업 안내](../Docs/TEAM_WORKFLOW.md)를 따릅니다. 맵 생성 스크립트를 실행하면 `Stage1/` 생성 액터를 다시 배치하므로, 수동으로 맵을 수정한 뒤에는 먼저 별도 브랜치·commit 또는 맵 사본을 만듭니다.
