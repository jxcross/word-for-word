"""
Streamlit 기반 Word-for-Word 번역 앱
- 왼쪽 창: 어절 버튼 클릭으로 텍스트 구성
- 오른쪽 창: 실시간 번역 결과 표시
"""

import streamlit as st
from typing import List, Tuple, Optional
from datetime import datetime
import text_processor
import translation
import storage


# 페이지 설정
st.set_page_config(
    page_title="Word-for-Word Translation",
    page_icon="🌐",
    layout="wide"
)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'source_lang' not in st.session_state:
        st.session_state.source_lang = 'ko'
    if 'target_lang' not in st.session_state:
        st.session_state.target_lang = 'en'
    if 'full_text' not in st.session_state:
        st.session_state.full_text = ''
    if 'sentences' not in st.session_state:
        st.session_state.sentences = []
    if 'current_sentence_idx' not in st.session_state:
        st.session_state.current_sentence_idx = 0
    if 'current_words' not in st.session_state:
        st.session_state.current_words = []
    if 'selected_words' not in st.session_state:
        st.session_state.selected_words = []
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = {}  # {sentence_idx: (original, translated)}
    elif isinstance(st.session_state.translation_history, list):
        # 기존 리스트 형식을 딕셔너리로 변환 (호환성)
        old_list = st.session_state.translation_history
        st.session_state.translation_history = {}
        for idx, (original, translated) in enumerate(old_list):
            st.session_state.translation_history[idx] = (original, translated)
    if 'deepl_api_key' not in st.session_state:
        st.session_state.deepl_api_key = ''
    if 'translator' not in st.session_state:
        st.session_state.translator = None
    if 'current_translation' not in st.session_state:
        st.session_state.current_translation = ''
    if 'previous_translation' not in st.session_state:
        st.session_state.previous_translation = ''
    if 'sentence_states' not in st.session_state:
        st.session_state.sentence_states = {}  # {sentence_idx: {'selected_words': [...], 'current_translation': '...', 'previous_translation': '...'}}


def save_current_sentence_state():
    """현재 문장의 상태를 저장"""
    if not st.session_state.sentences:
        return
    
    sentence_idx = st.session_state.current_sentence_idx
    st.session_state.sentence_states[sentence_idx] = {
        'selected_words': list(st.session_state.selected_words),
        'current_translation': st.session_state.current_translation,
        'previous_translation': st.session_state.previous_translation
    }


def restore_sentence_state(sentence_idx: int):
    """특정 문장의 상태를 복원"""
    if not st.session_state.sentences:
        return
    
    # 현재 문장의 어절 가져오기
    st.session_state.current_words = text_processor.get_current_sentence_words(
        st.session_state.sentences,
        sentence_idx
    )
    
    # 저장된 상태가 있으면 복원
    if sentence_idx in st.session_state.sentence_states:
        state = st.session_state.sentence_states[sentence_idx]
        st.session_state.selected_words = list(state.get('selected_words', []))
        st.session_state.current_translation = state.get('current_translation', '')
        st.session_state.previous_translation = state.get('previous_translation', '')
    else:
        # 저장된 상태가 없으면 초기화
        st.session_state.selected_words = []
        st.session_state.current_translation = ''
        st.session_state.previous_translation = ''


def reset_current_sentence():
    """현재 문장 상태 완전 초기화 (저장된 상태도 삭제)"""
    if not st.session_state.sentences:
        return
    
    sentence_idx = st.session_state.current_sentence_idx
    
    # 저장된 상태 삭제
    if sentence_idx in st.session_state.sentence_states:
        del st.session_state.sentence_states[sentence_idx]
    
    # 현재 문장의 어절 가져오기
    st.session_state.current_words = text_processor.get_current_sentence_words(
        st.session_state.sentences,
        sentence_idx
    )
    
    # 완전히 초기화
    st.session_state.selected_words = []
    st.session_state.current_translation = ''
    st.session_state.previous_translation = ''


def process_text_input(text: str):
    """텍스트 입력 처리"""
    if not text or not text.strip():
        st.warning("텍스트를 입력하세요.")
        return
    
    # 문장 분할
    sentences, detected_lang = text_processor.process_text(
        text, 
        st.session_state.source_lang
    )
    
    if not sentences:
        st.warning("문장을 찾을 수 없습니다.")
        return
    
    # 상태 업데이트
    st.session_state.full_text = text
    st.session_state.sentences = sentences
    st.session_state.current_sentence_idx = 0
    st.session_state.translation_history = {}
    st.session_state.sentence_states = {}  # 문장 상태 초기화
    
    # 언어 자동 감지 결과 반영
    if detected_lang:
        st.session_state.source_lang = detected_lang
        st.session_state.target_lang = 'en' if detected_lang == 'ko' else 'ko'
    
    # 현재 문장 초기화
    reset_current_sentence()
    
    st.success(f"{len(sentences)}개의 문장을 찾았습니다.")
    st.rerun()


def highlight_different_words(current: str, previous: str) -> str:
    """
    현재 번역 결과와 이전 번역 결과를 비교하여 새로 추가된 단어만 빨간색으로 표시합니다.
    
    Args:
        current: 현재 번역 결과
        previous: 이전 번역 결과
        
    Returns:
        HTML 형식의 텍스트 (새로 추가된 단어는 빨간색)
    """
    if not previous:
        # 이전 번역이 없으면 모든 단어를 빨간색으로 표시하지 않고 일반 텍스트로
        return current
    
    # 단어 단위로 분할
    current_words = text_processor.split_into_words(current)
    previous_words = text_processor.split_into_words(previous)
    
    # 이전 단어들을 집합으로 만들어 빠른 조회
    previous_words_set = set(previous_words)
    
    # 현재 단어들을 순회하면서 이전에 없던 단어만 빨간색으로 표시
    result_parts = []
    
    for current_word in current_words:
        # HTML 이스케이프 처리
        escaped_word = current_word.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # 이전 번역에 없는 단어면 빨간색으로 표시
        if current_word not in previous_words_set:
            result_parts.append(f'<span style="color: red; font-weight: bold;">{escaped_word}</span>')
        else:
            # 이전에 있던 단어는 일반 텍스트로 표시
            result_parts.append(escaped_word)
    
    return ' '.join(result_parts)


def handle_word_click(word_idx: int):
    """어절 버튼 클릭 처리 (토글)"""
    if word_idx < 0 or word_idx >= len(st.session_state.current_words):
        return
    
    word = st.session_state.current_words[word_idx]
    
    # 선택된 단어 인덱스 리스트
    selected_indices = [w[0] for w in st.session_state.selected_words]
    
    # 토글: 이미 선택된 단어면 제거, 아니면 추가
    current_selected = list(st.session_state.selected_words)
    if word_idx in selected_indices:
        # 선택 해제
        current_selected = [w for w in current_selected if w[0] != word_idx]
    else:
        # 선택 추가
        current_selected.append((word_idx, word))
    
    st.session_state.selected_words = current_selected
    
    # 누적 텍스트 생성 (순서대로 정렬)
    sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
    accumulated_text = ' '.join([w[1] for w in sorted_words])
    
    # 번역 수행
    if st.session_state.translator and accumulated_text:
        try:
            # 이전 번역 결과 저장
            st.session_state.previous_translation = st.session_state.current_translation
            
            translated = st.session_state.translator.translate(
                accumulated_text,
                st.session_state.source_lang,
                st.session_state.target_lang
            )
            st.session_state.current_translation = translated
        except translation.TranslationError as e:
            st.error(str(e))
            st.session_state.current_translation = ''


def translate_current_sentence():
    """현재 문장의 모든 어절을 선택하고 번역 수행"""
    if not st.session_state.sentences or not st.session_state.current_words:
        return
    
    # 모든 어절을 선택 상태로 만들기
    all_words = [(idx, word) for idx, word in enumerate(st.session_state.current_words)]
    st.session_state.selected_words = all_words
    
    # 전체 문장 텍스트 생성
    full_text = ' '.join(st.session_state.current_words)
    
    # 번역 수행
    if st.session_state.translator and full_text:
        try:
            # 이전 번역 결과 저장
            st.session_state.previous_translation = st.session_state.current_translation
            
            translated = st.session_state.translator.translate(
                full_text,
                st.session_state.source_lang,
                st.session_state.target_lang
            )
            st.session_state.current_translation = translated
        except translation.TranslationError as e:
            st.error(str(e))
            st.session_state.current_translation = ''


def save_current_sentence():
    """현재 문장 번역 저장 (번역 결과가 없어도 원문만으로 저장 가능)"""
    if not st.session_state.sentences:
        return
    
    current_sentence = st.session_state.sentences[st.session_state.current_sentence_idx]
    translation_text = st.session_state.current_translation or ''  # 번역 결과가 없으면 빈 문자열
    sentence_idx = st.session_state.current_sentence_idx
    
    if current_sentence:
        # 문장 인덱스를 키로 사용하여 저장 (중복 방지 및 업데이트)
        if sentence_idx in st.session_state.translation_history:
            st.session_state.translation_history[sentence_idx] = (current_sentence, translation_text)
            if translation_text:
                st.success("번역이 업데이트되었습니다.")
            else:
                st.success("원문이 저장되었습니다.")
        else:
            st.session_state.translation_history[sentence_idx] = (current_sentence, translation_text)
            if translation_text:
                st.success("번역이 저장되었습니다.")
            else:
                st.success("원문이 저장되었습니다.")


def move_to_next_sentence():
    """다음 문장으로 이동"""
    if not st.session_state.sentences:
        return
    
    # 현재 문장의 상태 저장 (선택된 단어, 번역 결과 등)
    save_current_sentence_state()
    
    # 현재 문장 저장 (번역 결과가 없어도 원문만으로 저장 가능)
    save_current_sentence()
    
    # 다음 문장으로 이동
    if st.session_state.current_sentence_idx < len(st.session_state.sentences) - 1:
        st.session_state.current_sentence_idx += 1
        restore_sentence_state(st.session_state.current_sentence_idx)
    else:
        st.info("마지막 문장입니다.")


def move_to_previous_sentence():
    """이전 문장으로 이동"""
    if st.session_state.current_sentence_idx > 0:
        # 현재 문장의 상태 저장 (선택된 단어, 번역 결과 등)
        save_current_sentence_state()
        
        # 현재 문장 저장 (번역 결과가 없어도 원문만으로 저장 가능)
        save_current_sentence()
        
        st.session_state.current_sentence_idx -= 1
        restore_sentence_state(st.session_state.current_sentence_idx)
    else:
        st.info("첫 번째 문장입니다.")


def initialize_translator(api_key: str):
    """번역기 초기화"""
    try:
        st.session_state.translator = translation.DeepLTranslator(api_key)
        st.session_state.deepl_api_key = api_key
        return True
    except translation.TranslationError as e:
        st.error(str(e))
        return False


def main():
    """메인 앱"""
    initialize_session_state()
    
    # 전역 CSS 스타일 추가
    st.markdown("""
    <style>
    /* 전역 스타일 */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --bg-color: #ffffff;
        --card-bg: #f8f9fa;
        --border-color: #dee2e6;
        --text-color: #212529;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --shadow-hover: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* 스크롤 동작 개선 - 화면 점프 방지 */
    html {
        scroll-behavior: smooth;
    }
    
    /* 제목 스타일 */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--primary-color) !important;
        margin-bottom: 1rem !important;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
    }
    
    /* 본문 텍스트 */
    .stMarkdown p, .stText {
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: var(--text-color) !important;
    }
    
    /* 카드 스타일 컨테이너 */
    .card-container {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        transition: box-shadow 0.3s ease;
    }
    
    .card-container:hover {
        box-shadow: var(--shadow-hover);
    }
    
    /* 버튼 스타일 개선 */
    .stButton > button {
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-hover) !important;
    }
    
    /* 선택된 버튼 스타일 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
    }
    
    /* 번역 결과 박스 */
    .translation-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: 2px solid var(--primary-color);
        border-radius: 12px;
        padding: 1.5rem;
        min-height: 120px;
        font-size: 1.1rem;
        line-height: 1.8;
        box-shadow: var(--shadow);
    }
    
    /* 선택된 텍스트 박스 */
    .selected-text-box {
        background-color: #e3f2fd;
        border: 2px solid #2196f3;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* 어절 버튼 그리드 */
    .word-button-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px 8px 0 0 !important;
    }
    
    /* 진행 상황 표시 */
    .progress-container {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 정보 메시지 스타일 */
    .stInfo {
        background-color: #e3f2fd !important;
        border-left: 4px solid #2196f3 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* 성공 메시지 스타일 */
    .stSuccess {
        background-color: #e8f5e9 !important;
        border-left: 4px solid #4caf50 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* 경고 메시지 스타일 */
    .stWarning {
        background-color: #fff3e0 !important;
        border-left: 4px solid #ff9800 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* 에러 메시지 스타일 */
    .stError {
        background-color: #ffebee !important;
        border-left: 4px solid #f44336 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* 번역 완료 영역 */
    .translation-history-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: 2px solid var(--success-color);
        border-radius: 12px;
        padding: 1.5rem;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 1rem;
        line-height: 1.8;
        box-shadow: var(--shadow);
    }
    
    /* 네비게이션 버튼 컨테이너 */
    .nav-container {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 2px solid var(--border-color);
    }
    
    /* 캡션 스타일 */
    .stCaption {
        font-size: 0.95rem !important;
        color: #6c757d !important;
        font-weight: 500 !important;
    }
    
    /* 텍스트 영역 스타일 */
    .stTextArea > div > div > textarea {
        font-size: 1rem !important;
        line-height: 1.6 !important;
        border-radius: 8px !important;
        border: 2px solid var(--border-color) !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1) !important;
    }
    
    /* 구분선 스타일 */
    hr {
        margin: 2rem 0 !important;
        border: none !important;
        border-top: 2px solid var(--border-color) !important;
    }
    
    /* 스크롤바 스타일 (선택사항) */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 메인 컨테이너로 감싸서 화면 점프 방지
    main_container = st.container()
    
    #with main_container:
        # 제목
        #st.markdown("<h2>🌐 Word-for-Word Translation</h2>", unsafe_allow_html=True)
        #st.markdown("---")
    
    # 사이드바: 설정
    with st.sidebar:

        st.markdown("""
<div style="text-align: center;">
    <div style="font-size: 28px; font-weight: 600; line-height: 1.1;">
        🌐 Word-for-Word Translation
    </div>
    <div style="font-size: 18px; line-height: 1.1;">
        직 독 직 해
    </div>
</div>
""", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("<h3>⚙️ 설정</h3>", unsafe_allow_html=True)
        
        # DeepL API 키 입력
        with st.container():
            st.markdown("**🔑 DeepL API 키**", unsafe_allow_html=True)
            api_key_input = st.text_input(
                "API 키",
                value=st.session_state.deepl_api_key,
                type="password",
                help="DeepL API 키를 입력하세요. .env 파일에서도 로드됩니다.",
                label_visibility="visible"
            )
            
            if api_key_input and api_key_input != st.session_state.deepl_api_key:
                if initialize_translator(api_key_input):
                    st.success("✅ API 키가 설정되었습니다.")
            
            if st.session_state.translator:
                st.success("✅ 번역기 준비됨")
            else:
                st.warning("⚠️ API 키를 설정하세요")
        
        st.markdown("---")
        
        # 진행 상황
        # if st.session_state.sentences:
        #     with st.container():
        #         st.markdown("**📊 진행 상황**", unsafe_allow_html=True)
        #         total = len(st.session_state.sentences)
        #         current = st.session_state.current_sentence_idx + 1
        #         progress_value = current / total if total > 0 else 0
        #         st.progress(progress_value)
        #         st.markdown(f"<div class='progress-container'><strong>현재:</strong> {current} / {total} 문장<br><strong>완료:</strong> {len(st.session_state.translation_history)} 문장</div>", unsafe_allow_html=True)
        
        #     st.markdown("---")

        # 언어 선택
        with st.container():
            st.markdown("**🌍 번역 방향**")
            translation_direction = st.selectbox(
                "번역 방향을 선택하세요",
                ["한국어 🇰🇷 → 영어 🇬🇧", "영어 🇬🇧 → 한국어 🇰🇷"],
                index=0 if st.session_state.source_lang == 'ko' else 1,
                label_visibility="collapsed"
            )
            
            if translation_direction == "한국어 🇰🇷 → 영어 🇬🇧":
                st.session_state.source_lang = 'ko'
                st.session_state.target_lang = 'en'
            else:
                st.session_state.source_lang = 'en'
                st.session_state.target_lang = 'ko'
        
        st.markdown("---")
        
        # 텍스트 입력
        with st.container():
            st.markdown("**📝 텍스트 입력**", unsafe_allow_html=True)
            
            # 파일 업로드
            uploaded_file = st.file_uploader(
                "📄 텍스트 파일 업로드",
                type=['txt'],
                help="한국어 또는 영어 텍스트 파일을 업로드하세요."
            )
            
            if uploaded_file is not None:
                text = uploaded_file.read().decode('utf-8')
                if text != st.session_state.full_text:
                    process_text_input(text)
            
            # 텍스트 붙여넣기
            text_input = st.text_area(
                "✍️ 또는 텍스트를 붙여넣으세요",
                height=120,
                help="텍스트를 직접 입력하거나 붙여넣으세요.",
                placeholder="여기에 텍스트를 입력하거나 붙여넣으세요..."
            )
            
            if st.button("🚀 텍스트 처리", type="primary", use_container_width=True):
                if text_input:
                    process_text_input(text_input)
                else:
                    st.warning("⚠️ 텍스트를 입력하세요.")
    
    # 메인 영역
    with main_container:
        # 번역 영역
        if st.session_state.sentences:
            #st.markdown("---")
            #st.markdown("<h3>🔄 번역 작업</h3>", unsafe_allow_html=True)
            
            # 현재 문장 정보 카드
            current_sentence = st.session_state.sentences[st.session_state.current_sentence_idx]
            sentence_info = st.container()
            with sentence_info:
                st.markdown(
                    f"<div class='card-container' style='text-align: center; padding: 1rem;'>"
                    f"<strong style='font-size: 1.0rem;'>📄 문장 {st.session_state.current_sentence_idx + 1} / {len(st.session_state.sentences)}</strong>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            
            # 오른쪽 메인 영역: 번역과 번역 완료 탭
            tab1, tab2 = st.tabs(["🔄 실시간 번역", "✅ 번역 완료 목록"])
            
            with tab1:
                # 번역 탭 안에 원문과 번역을 나란히 표시
                left_col, right_col = st.columns([1, 1], gap="large")
                
                with left_col:
                    translation_left = st.container()
                    with translation_left:
                        st.markdown("**📖 원문**", unsafe_allow_html=True)
                        
                        # 선택된 어절들 표시
                        if st.session_state.selected_words:
                            # 선택된 단어들을 순서대로 정렬
                            sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                            selected_text = ' '.join([w[1] for w in sorted_words])
                            st.markdown(
                                f'<div class="selected-text-box">'
                                f'<strong style="font-size: 1.0rem; color: #1f77b4;">✨ 선택된 텍스트:</strong><br>'
                                f'{selected_text}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        
                        # 어절 버튼들 (토글)
                        st.markdown("<p style='font-size: 1.05rem; margin-top: 1rem;'><strong>👆 어절을 클릭하여 선택/해제하세요:</strong></p>", unsafe_allow_html=True)
                        
                        if st.session_state.current_words:
                            # 선택된 단어 인덱스 리스트
                            selected_indices = [w[0] for w in st.session_state.selected_words]
                            
                            # 버튼을 그리드로 배치
                            cols_per_row = 4
                            
                            # 모든 어절을 버튼으로 표시 (선택된 것은 강조)
                            word_buttons_container = st.container()
                            with word_buttons_container:
                                for row_start in range(0, len(st.session_state.current_words), cols_per_row):
                                    cols = st.columns(cols_per_row, gap="small")
                                    for col_idx, col in enumerate(cols):
                                        word_idx = row_start + col_idx
                                        if word_idx < len(st.session_state.current_words):
                                            word = st.session_state.current_words[word_idx]
                                            button_key = f"word_btn_{st.session_state.current_sentence_idx}_{word_idx}"
                                            
                                            # 선택된 단어는 primary 타입으로 표시
                                            is_selected = word_idx in selected_indices
                                            button_label = f"✓ {word}" if is_selected else word
                                            button_clicked = col.button(
                                                button_label,
                                                key=button_key,
                                                use_container_width=True,
                                                type="primary" if is_selected else "secondary"
                                            )
                                            if button_clicked:
                                                handle_word_click(word_idx)
                                                # 상태 업데이트 후 rerun 필요 (UI 반영)
                                                st.rerun()
                        else:
                            st.info("ℹ️ 어절이 없습니다.")
                
                with right_col:
                    translation_right = st.container()
                    with translation_right:
                        st.markdown("**🌍 번역 결과**", unsafe_allow_html=True)
                        
                        # 번역 결과 표시
                        if st.session_state.current_translation:
                            # 달라진 단어를 빨간색으로 표시
                            highlighted = highlight_different_words(
                                st.session_state.current_translation,
                                st.session_state.previous_translation
                            )
                            st.markdown(
                                f'<div class="translation-box" style="margin-bottom: 1rem;">'
                                f'<strong style="font-size: 1.0rem; color: #1f77b4;">✨ 번역 결과:</strong><br>'
                                f'{highlighted}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        elif st.session_state.selected_words:
                            st.info("💡 어절을 클릭하면 번역이 표시됩니다.")
                        else:
                            st.info("👆 왼쪽에서 어절을 선택하면 번역이 표시됩니다.")
                        
                        # 번역 버튼 (수동 번역)
                        if st.session_state.selected_words and st.session_state.translator:
                            # 선택된 단어들을 순서대로 정렬
                            sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                            accumulated_text = ' '.join([w[1] for w in sorted_words])
                            refresh_col1, refresh_col2 = st.columns([2, 1])
                            with refresh_col1:
                                if st.button("🔄 번역 새로고침", use_container_width=True, type="primary"):
                                    try:
                                        # 이전 번역 결과 저장
                                        st.session_state.previous_translation = st.session_state.current_translation
                                        
                                        translated = st.session_state.translator.translate(
                                            accumulated_text,
                                            st.session_state.source_lang,
                                            st.session_state.target_lang
                                        )
                                        st.session_state.current_translation = translated
                                        st.rerun()
                                    except translation.TranslationError as e:
                                        st.error(str(e))
            
            with tab2:
                translation_history_container = st.container()
                with translation_history_container:
                    #st.markdown("<h3>✅ 번역 완료 목록</h3>", unsafe_allow_html=True)
                    
                    # 번역된 내용 표시
                    if st.session_state.translation_history:
                        st.markdown(
                            f"<div class='card-container' style='text-align: center;'>"
                            f"<strong style='font-size: 1.0rem;'>📊 번역 완료된 문장 수: {len(st.session_state.translation_history)}</strong>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        #st.markdown("---")
                        
                        # 번역된 내용을 표시 (인덱스 순서대로 정렬)
                        translation_text = ""
                        # translation_history가 딕셔너리인지 확인
                        if isinstance(st.session_state.translation_history, dict):
                            # 문장 인덱스 순서대로 정렬
                            sorted_items = sorted(st.session_state.translation_history.items())
                            
                            # 모든 항목 표시
                            for display_idx, (sentence_idx, value) in enumerate(sorted_items, 1):
                                # value가 튜플인지 확인
                                if isinstance(value, tuple) and len(value) == 2:
                                    original, translated = value
                                    translation_text += f"{display_idx}. {original} | {translated}\n"
                                else:
                                    # 예상치 못한 형식
                                    translation_text += f"{display_idx}. [오류: 잘못된 데이터 형식] (인덱스: {sentence_idx}, 값: {value})\n"
                        else:
                            # 리스트 형식인 경우 (호환성)
                            for idx, item in enumerate(st.session_state.translation_history, 1):
                                if isinstance(item, tuple) and len(item) == 2:
                                    original, translated = item
                                    translation_text += f"{idx}. {original} | {translated}\n"
                                else:
                                    translation_text += f"{idx}. [오류: 잘못된 데이터 형식]\n"
                        
                        # HTML 이스케이프 처리
                        import html
                        translation_text_escaped = html.escape(translation_text)
                        # 줄바꿈을 HTML <br>로 변환하여 표시
                        translation_text_html = translation_text_escaped.replace('\n', '<br>')
                        st.markdown(
                            f'<div class="translation-history-box" style="margin-bottom: 1rem;">{translation_text_html}</div>',
                            unsafe_allow_html=True
                        )
                        
                        # 전체 번역 저장 버튼 및 다운로드 버튼
                        save_col1, save_col2 = st.columns([1, 1])
                        with save_col1:
                            if st.button("💾 전체 번역 저장", use_container_width=True, type="primary"):
                                try:
                                    # 딕셔너리를 리스트로 변환 (storage 함수 호환성)
                                    translation_list = list(st.session_state.translation_history.values())
                                    filepath = storage.save_translation(translation_list)
                                    st.success(f"✅ 번역이 저장되었습니다: {filepath}")
                                except Exception as e:
                                    st.error(f"❌ 저장 중 오류: {str(e)}")
                        
                        with save_col2:
                            # 다운로드용 텍스트 생성
                            if st.session_state.translation_history:
                                # 딕셔너리를 정렬
                                sorted_translations = sorted(
                                    st.session_state.translation_history.items()
                                )
                                
                                # 다운로드용 텍스트 생성
                                download_text = ""
                                for sentence_idx, (original, translated) in sorted_translations:
                                    download_text += f"{original} | {translated}\n"
                                
                                # 파일명 생성
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"translation_{timestamp}.txt"
                                
                                st.download_button(
                                    label="📥 다운로드",
                                    data=download_text,
                                    file_name=filename,
                                    mime="text/plain",
                                    use_container_width=True,
                                    type="primary"
                                )
                            else:
                                st.button("📥 다운로드", use_container_width=True, disabled=True, type="primary")
                    else:
                        st.info("ℹ️ 아직 번역 완료된 문장이 없습니다. 번역 탭에서 작업을 진행하세요.")
        
            # 네비게이션 버튼
            nav_container = st.container()
            with nav_container:
                st.markdown("<div class='nav-container'></div>", unsafe_allow_html=True)
                #st.markdown("---")
                
                # 현재 문장 인덱스와 전체 문장 수
                current_idx = st.session_state.current_sentence_idx
                total_sentences = len(st.session_state.sentences)
                is_first_sentence = current_idx == 0
                is_last_sentence = current_idx == total_sentences - 1
                
                nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1], gap="medium")
                
                with nav_col1:
                    if st.button("◀️ 이전 문장", use_container_width=True, disabled=is_first_sentence, key="nav_prev"):
                        move_to_previous_sentence()
                        st.rerun()
                
                with nav_col2:
                    # 마지막 문장인 경우 "저장" 버튼, 그 외에는 "다음 문장" 버튼
                    if is_last_sentence:
                        button_text = "💾 저장"
                    else:
                        button_text = "다음 문장 ▶️"
                    
                    if st.button(button_text, use_container_width=True, type="primary", key="nav_next"):
                        if is_last_sentence:
                            # 마지막 문장: 저장만 수행 (번역 결과가 없어도 저장 가능)
                            save_current_sentence()
                        else:
                            # 그 외: 저장 후 다음 문장으로 이동
                            move_to_next_sentence()
                        st.rerun()
                
                with nav_col3:
                    if st.button("🌐 문장 번역", use_container_width=True, key="nav_translate"):
                        if st.session_state.translator:
                            translate_current_sentence()
                            st.rerun()
                        else:
                            st.warning("⚠️ 번역기를 설정하세요.")
                        
                with nav_col4:
                    if st.button("🔄 현재 문장 리셋", use_container_width=True, key="nav_reset"):
                        reset_current_sentence()
                        st.rerun()
        
        else:
            # 안내 메시지
            welcome_container = st.container()
            with welcome_container:
                st.markdown(
                    "<div class='card-container' style='text-align: center; padding: 3rem;'>"
                    "<h2 style='color: #667eea;'>👋 환영합니다!</h2>"
                    "<p style='font-size: 1.2rem; margin-top: 1rem;'>"
                    "👆 왼쪽 사이드바에서 텍스트 파일을 업로드하거나<br>"
                    "텍스트를 직접 입력하여 번역을 시작하세요."
                    "</p>"
                    "</div>",
                    unsafe_allow_html=True
                )


if __name__ == "__main__":
    main()
