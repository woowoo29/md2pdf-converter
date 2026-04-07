# 앱 아이콘 제작 가이드

이 프로젝트의 아이콘 작업은 아래 순서로 진행합니다.

1. AI로 고해상도 아이콘 시안을 생성합니다.
2. Figma에서 다듬어 macOS 앱 아이콘처럼 정리합니다.
3. 최종 `1024x1024` PNG로 내보냅니다.
4. 그 PNG를 `md2pdf-converter.icns`로 변환합니다.
5. 앱을 다시 빌드해서 아이콘이 자동으로 반영되게 합니다.

## 추천 방향

이 앱에 가장 잘 맞는 방향은 다음과 같습니다.

- `문서 -> PDF 변환`이 한눈에 느껴질 것
- 장난스럽기보다 깔끔하고 프리미엄한 분위기
- 작은 크기에서도 형태가 잘 읽힐 것
- "작은 유틸리티 앱"답게 현대적이고 정돈된 인상일 것

추천 컨셉 요소:

- 접힌 모서리가 있는 흰색 문서 시트
- 문서 안에 들어간 은은한 Markdown 흔적 (`#`, 리스트 줄, 코드 느낌)
- 완성된 PDF로 바뀌는 흐름이 느껴지는 방향성 요소
- 블루 계열 중심 팔레트 + 작은 웜 포인트 색상

이 방향이 일반적인 파일 아이콘이나 단순 이니셜 로고보다, 앱 성격을 더 잘 설명해줍니다.

## 아이콘 컨셉 3안

### 1. 문서 변환 아이콘 (추천)

- 접힌 모서리가 있는 흰색 문서
- 왼쪽에는 Markdown 느낌의 기호나 줄
- 오른쪽으로 갈수록 더 정리된 PDF처럼 보이는 변화
- 블루 + 그래파이트 기반, 코럴 포인트 색상

장점:

- "Markdown -> PDF" 기능이 바로 전달됨
- 작은 크기에서도 읽히기 좋음
- 그냥 예쁜 그림이 아니라 실제 유틸리티 앱 아이콘처럼 보임

### 2. M -> P 변환 타일

- 둥근 사각형 타일
- `M`이 `P`로 바뀌는 느낌의 심볼
- 더 로고스럽고 단순한 방향

장점:

- 간결하고 브랜드처럼 보이기 쉬움
- 아이콘이 단정하게 정리되기 좋음

단점:

- 처음 보는 사람에게 기능 설명력은 조금 약함

### 3. 종이 스택 + 내보내기 포인트

- 겹쳐진 두 장의 종이
- 위쪽은 Markdown 초안 느낌
- 아래쪽은 정리된 PDF 느낌
- 작은 반짝임이나 방향 요소로 export 감각 추가

장점:

- before / after 흐름이 보임
- 잘 다듬으면 꽤 고급스럽게 나올 수 있음

단점:

- 요소가 많아지면 금방 복잡해질 수 있음

## AI 프롬프트

이미지 생성은 보통 영문 프롬프트가 더 안정적이므로, 아래 문장을 기본 프롬프트로 사용하는 것을 추천합니다.

```text
Design a premium macOS app icon for a utility called md2pdf-converter. Show a clean white document sheet with a folded corner, subtle Markdown cues on the page, and a clear visual sense of transformation into a polished PDF document. Use a cobalt blue and deep graphite palette with a small warm coral accent. The icon should feel modern, crisp, professional, and slightly tactile, with strong silhouette clarity at small sizes. Keep it centered, simple, and elegant. No words, no letters as the main focus, no busy background, no photorealism, no mockup, no browser UI, no shadows outside the icon shape. 1024x1024, macOS app icon style.
```

원하시면 이 기본 프롬프트를 바탕으로 더 미니멀한 버전, 더 입체적인 버전, 더 문서 중심인 버전으로 파생 프롬프트를 만들어도 좋습니다.

## Figma 정리 체크리스트

AI 시안이 어느 정도 괜찮게 나오면, Figma에서 아래 순서로 다듬습니다.

1. `1024x1024` 프레임 위에 배치합니다.
2. 작은 크기에서 뭉개질 디테일은 줄입니다.
3. 전체 실루엣이 더 또렷하게 보이도록 정리합니다.
4. `64x64` 정도로 축소해도 문서 형태가 읽히는지 확인합니다.
5. 탁한 그라데이션이나 과한 질감은 줄입니다.
6. 대표 블루 1개, 짙은 중성색 1개, 포인트 색상 1개 정도로 색을 정리합니다.
7. 최종 파일을 아래 경로로 내보냅니다.

```text
assets/icon/source/md2pdf-icon-1024.png
```

## PNG를 `.icns`로 변환하기

프로젝트 루트에서 아래 명령어를 실행합니다.

```bash
bash scripts/build_icns.sh
```

그러면 아래 파일이 생성됩니다.

```text
assets/icon/md2pdf-converter.icns
```

## 앱 다시 빌드하기

`.icns` 파일이 준비되면, 앱 빌드 시 자동으로 아이콘이 포함됩니다.

```bash
bash scripts/build_macos_app.sh
```

추가 설정은 필요 없습니다.
