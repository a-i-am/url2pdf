# GitHub PAT 및 Repository Secret 설정 가이드

이 문서는 Private 저장소 `url2pdf-project`에서 Public 저장소 `url2pdf-public`으로 코드를 미러링하기 위해 `PUBLIC_REPO_PAT` Secret을 설정하는 절차를 정리합니다.

## 1. Personal Access Token 발급

### 1.1 Fine-grained token 권장

1. GitHub에 로그인합니다.
2. 우측 상단 프로필 아이콘을 클릭합니다.
3. `Settings`로 이동합니다.
4. 좌측 메뉴 하단의 `Developer settings`로 이동합니다.
5. `Personal access tokens` > `Fine-grained tokens`를 선택합니다.
6. `Generate new token`을 클릭합니다.
7. token 이름을 입력합니다.
   - 예: `url2pdf-public-mirror`
8. `Expiration`을 설정합니다.
   - 운영 편의와 보안을 함께 고려해 만료일을 지정하는 것을 권장합니다.
9. `Repository access`에서 `Only select repositories`를 선택합니다.
10. 대상 Public 저장소 `url2pdf-public`을 선택합니다.
11. `Repository permissions`에서 아래 권한을 설정합니다.
    - `Contents`: `Read and write`
12. `Generate token`을 클릭합니다.
13. 발급된 token 값을 복사합니다.

> token 값은 생성 직후 한 번만 확인할 수 있습니다. 복사한 값은 GitHub Secret 등록 전까지 안전하게 보관합니다.

### 1.2 Classic token을 사용하는 경우

Fine-grained token 사용이 어려운 경우 classic token을 사용할 수 있습니다.

1. GitHub `Settings` > `Developer settings`로 이동합니다.
2. `Personal access tokens` > `Tokens (classic)`을 선택합니다.
3. `Generate new token` > `Generate new token (classic)`을 클릭합니다.
4. token 이름과 만료일을 설정합니다.
5. Public 저장소에 push할 수 있도록 `public_repo` scope를 선택합니다.
6. `Generate token`을 클릭합니다.
7. 발급된 token 값을 복사합니다.

## 2. Private 저장소에 Secret 등록

1. GitHub에서 Private 저장소 `url2pdf-project`로 이동합니다.
2. 저장소 상단 메뉴에서 `Settings`를 클릭합니다.
3. 좌측 메뉴에서 `Secrets and variables` > `Actions`를 선택합니다.
4. `Repository secrets` 영역에서 `New repository secret`을 클릭합니다.
5. `Name`에 아래 값을 입력합니다.

```text
PUBLIC_REPO_PAT
```

6. `Secret` 값에 앞에서 발급받은 PAT 값을 붙여넣습니다.
7. `Add secret`을 클릭해 저장합니다.

## 3. 동작 확인

설정이 끝나면 Private 저장소에서 `v*` 형식의 Git tag를 push할 때 workflow가 실행됩니다.

예시는 다음과 같습니다.

```powershell
git tag v1.0
git push origin v1.0
```

workflow가 성공하면 `url2pdf-public` 저장소의 `main` 브랜치로 코드가 push됩니다.

## 4. 문제 해결 체크리스트

- Secret 이름이 정확히 `PUBLIC_REPO_PAT`인지 확인합니다.
- PAT가 `url2pdf-public` 저장소에 접근할 수 있는지 확인합니다.
- PAT에 `Contents: Read and write` 권한이 있는지 확인합니다.
- workflow 실행 로그에서 인증 오류가 발생하면 PAT 만료 여부를 확인합니다.
- tag 이름이 `v1.0`, `v2.3.4`처럼 `v`로 시작하는지 확인합니다.
