# Word-for-Word Translation App

영어와 한국어를 직독직해 방식으로 번역하는 Streamlit 기반 웹 애플리케이션입니다.

## 주요 기능

- 📝 **텍스트 입력**: 파일 업로드 또는 직접 붙여넣기
- 🔤 **어절 단위 분할**: 띄어쓰기 기준으로 문장을 어절로 분할
- 🖱️ **인터랙티브 번역**: 어절 버튼을 클릭하면 실시간으로 번역 결과 표시
- 💾 **번역 저장**: 완료된 번역을 텍스트 파일로 저장
- 🌐 **양방향 번역**: 한국어→영어, 영어→한국어 모두 지원

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/jxcross/word-for-word.git
cd word-for-word
```

### 2. 가상 환경 생성 및 활성화 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. DeepL API 키 설정

DeepL API 키를 발급받으려면 [DeepL Pro API](https://www.deepl.com/pro-api)를 방문하세요.

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```
DEEPL_API_KEY=your_api_key_here
```

또는 앱 실행 시 사이드바에서 직접 입력할 수 있습니다.

## 실행 방법

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 앱을 사용할 수 있습니다.

## 사용 방법

### 1. 초기 설정

- 사이드바에서 번역 방향 선택 (한국어→영어 또는 영어→한국어)
- DeepL API 키 입력 (또는 .env 파일에서 자동 로드)

### 2. 텍스트 입력

- **방법 1**: 텍스트 파일 업로드 (.txt 파일)
- **방법 2**: 텍스트 영역에 직접 붙여넣기

### 3. 어절 단위 번역

1. 왼쪽 창에서 어절 버튼을 순서대로 클릭
2. 클릭한 어절은 텍스트로 변환되어 왼쪽 상단에 표시
3. 오른쪽 창에 누적된 텍스트의 번역 결과가 실시간으로 표시
4. 예: "나는" → "I", "나는 요즘" → "Lately, I've been", "나는 요즘 바쁘다." → "I've been busy lately."

### 4. 문장 이동 및 저장

- **이전 문장**: 이전 문장으로 이동
- **다음 문장**: 다음 문장으로 이동 (현재 문장 자동 저장)
- **현재 문장 저장**: 현재 문장의 번역을 저장
- **전체 번역 저장**: 완료된 모든 번역을 텍스트 파일로 저장

### 5. 저장 형식

번역 결과는 `translations/` 디렉토리에 다음 형식으로 저장됩니다:

```
원문 문장 1 | Translated sentence 1
원문 문장 2 | Translated sentence 2
...
```

## 프로젝트 구조

```
word-for-word/
├── app.py                 # Streamlit 메인 앱
├── translation.py         # DeepL API 번역 모듈
├── text_processor.py      # 문장/어절 분할 처리
├── storage.py            # 번역 결과 저장 기능
├── requirements.txt      # 의존성 패키지
├── .env.example         # 환경 변수 예시
└── README.md            # 사용 설명서
```

## 기술 스택

- **Streamlit**: 웹 애플리케이션 프레임워크
- **DeepL API**: 고품질 번역 서비스
- **Python 3.8+**: 프로그래밍 언어

## 주의사항

- DeepL API는 유료 서비스입니다. 무료 플랜도 제공되지만 사용량 제한이 있습니다.
- API 키는 안전하게 보관하세요. `.env` 파일은 `.gitignore`에 포함되어 있습니다.
- 한국어 문장은 띄어쓰기 기준으로 어절이 분할됩니다. 띄어쓰기가 없는 경우 형태소 분석이 필요할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요. Pull Request도 환영합니다!