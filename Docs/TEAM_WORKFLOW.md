# Team workflow

프로젝트 설치와 첫 실행은 [README의 처음 실행](../README.md#처음-실행)을 참고합니다.

## 저장소 범위

Git의 최상위는 `GraduationProject/`입니다. `MuseumStage1Demo/` 안에 별도의 Git 저장소를 만들지 않습니다. 앞으로 추가할 공용 에셋과 다른 작업도 최상위 저장소에서 함께 관리합니다.

## 변경을 공유할 때

1. 시작 전에 언리얼을 닫고 최신 변경을 pull합니다.
2. 담당 작업용 브랜치에서 수정합니다.
3. 언리얼에서 저장하고, 변경 파일 목록을 확인합니다.
4. 해당 작업의 파일을 commit한 뒤 push합니다.
5. 팀의 검토 방식에 맞춰 main에 반영합니다.

`.umap`, `.uasset`, `.blend`, `.fbx`는 텍스트처럼 변경을 자동 병합하기 어렵습니다. 같은 맵·블루프린트·모델 파일을 동시에 수정하지 않도록 담당자를 정합니다. Git LFS는 큰 파일 관리용이며 동시 편집 충돌을 자동으로 해결하지 않습니다.

## 커밋할 파일 확인

새 에셋을 추가할 때는 필요한 설정·코드·반입 원본도 함께 확인합니다. 폴더별 용도와 작업 위치는 [README](../README.md)를 참고합니다.

`Saved`, `Intermediate`, `DerivedDataCache`, `Binaries`, 백업, 로그, 검사 결과, 배포 ZIP은 올리지 않습니다. 실행 데모는 패키징 결과물 전체를 별도 배포 경로로 전달합니다.

외부 자료를 사용하면 [외부 자료 기록](EXTERNAL_RESOURCES.md)에 출처와 사용 내용을 적고 관련 변경과 함께 커밋합니다.

## 참고

- [Git LFS 설정](https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage?platform=windows)
- [Unreal 폴더 구조](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-directory-structure)
