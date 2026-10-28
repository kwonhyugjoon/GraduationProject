# GraduationProject

졸업작품 전체를 관리하는 팀 공유 저장소입니다. 현재는 1스테이지 이동 데모와 최신 순찰자 모델 원본을 포함합니다.

초기 버전: **AI를 사용한 1차 데모 — 1스테이지 맵과 맵 이동만 구현**

```text
GraduationProject/
├─ MuseumStage1Demo/           Unreal Engine 프로젝트
│  ├─ MuseumStage1Demo.uproject
│  ├─ Config/                 공통 프로젝트 설정
│  ├─ Content/                맵·블루프린트·재질·플레이어·애니메이션
│  ├─ Source/                 달리기·손 장비 C++ 컴포넌트
│  ├─ Scripts/                맵 생성·모델 반입·검사 도구
│  └─ References/FirstPersonBody/  1인칭용 파생 FBX
├─ Assets/Player/night_patrol_v15/  최신 Blender·FBX 편집 원본
├─ Assets/Player/PatrolEquipment/  손전등·노트 및 손 모델 원본
├─ Docs/TEAM_WORKFLOW.md      Git 및 공동 작업 방법
├─ .gitignore
└─ .gitattributes
```

## 처음 실행

1. **Unreal Engine 5.7.4**, **Git**, **Git LFS**, **Visual Studio 2022**의 **C++를 사용한 게임 개발** 워크로드와 **.NET Framework 4.8 SDK**를 준비합니다.
2. Git LFS를 설치한 상태에서 저장소를 clone합니다. 웹사이트의 Download ZIP 대신 Git clone을 사용합니다.
3. 저장소 최상위에서 `git lfs install --local`을 실행한 뒤 `git lfs pull`로 에셋을 받습니다.
4. 한글이 없는 경로에 저장소를 두고 `MuseumStage1Demo/MuseumStage1Demo.uproject`를 엽니다. 모듈 빌드 안내가 나오면 빌드한 뒤 Play를 누릅니다.

첫 실행에는 셰이더와 캐시를 다시 만드는 시간이 필요합니다.

| 입력 | 동작 |
|---|---|
| WASD / 마우스 | 이동 / 시점 |
| Space / Shift 유지 | 점프 / 달리기 |
| 1 / 2 / 3 | 손전등 / 인수인계 노트 / 맨손 |
| 마우스 좌클릭 | 손전등을 든 상태에서 켜기·끄기 |

손전등은 처음에 켜진 상태이며 장비를 바꿔도 스위치 상태를 기억합니다. 야간 조명은 손전등을 사용하는 순찰에 맞춰 낮췄습니다.

현재 공유본에는 티라노와 기획서·맵 이미지를 포함하지 않습니다. 이 Windows 데모에서는 로컬 보안 토큰을 자동 생성하는 AndroidFileServer를 비활성화하고 관련 개인 설정을 제외했습니다.

## 작업 위치

`MuseumStage1Demo/Content/Stage1/Maps/L_MuseumStage1.umap`이 현재 맵입니다. 공용 캐릭터 원본은 `Assets/Player/night_patrol_v15/`에서 편집합니다.

실행 데모를 만들 때는 언리얼에서 패키징하고 출력 폴더를 `MuseumStage1Demo/Build/PlayableDemo/`로 지정합니다.

## 관련 문서

- [협업 절차와 Git 관리 규칙](Docs/TEAM_WORKFLOW.md)
- [외부 자료 기록](Docs/EXTERNAL_RESOURCES.md)
- [맵 생성·모델 반입·검사 도구](MuseumStage1Demo/Scripts/README.md)
