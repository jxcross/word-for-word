"""
Streamlit 기반 Word-for-Word 번역 앱
- 왼쪽 창: 어절 버튼 클릭으로 텍스트 구성
- 오른쪽 창: 실시간 번역 결과 표시
"""

import streamlit as st
from typing import List, Tuple, Optional
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
        st.session_state.translation_history = []
    if 'deepl_api_key' not in st.session_state:
        st.session_state.deepl_api_key = ''
    if 'translator' not in st.session_state:
        st.session_state.translator = None
    if 'current_translation' not in st.session_state:
        st.session_state.current_translation = ''


def reset_current_sentence():
    """현재 문장 상태 초기화"""
    # 새 리스트 생성하여 상태 업데이트
    st.session_state.selected_words = []
    st.session_state.current_translation = ''
    if st.session_state.sentences:
        st.session_state.current_words = text_processor.get_current_sentence_words(
            st.session_state.sentences,
            st.session_state.current_sentence_idx
        )


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
    st.session_state.translation_history = []
    
    # 언어 자동 감지 결과 반영
    if detected_lang:
        st.session_state.source_lang = detected_lang
        st.session_state.target_lang = 'en' if detected_lang == 'ko' else 'ko'
    
    # 현재 문장 초기화
    reset_current_sentence()
    
    st.success(f"{len(sentences)}개의 문장을 찾았습니다.")
    st.rerun()


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
            translated = st.session_state.translator.translate(
                accumulated_text,
                st.session_state.source_lang,
                st.session_state.target_lang
            )
            st.session_state.current_translation = translated
        except translation.TranslationError as e:
            st.error(str(e))
            st.session_state.current_translation = ''


def save_current_sentence():
    """현재 문장 번역 저장"""
    if not st.session_state.sentences:
        return
    
    current_sentence = st.session_state.sentences[st.session_state.current_sentence_idx]
    translation_text = st.session_state.current_translation
    
    if current_sentence and translation_text:
        # 번역 히스토리에 추가
        st.session_state.translation_history.append((current_sentence, translation_text))
        st.success("번역이 저장되었습니다.")


def move_to_next_sentence():
    """다음 문장으로 이동"""
    if not st.session_state.sentences:
        return
    
    # 현재 문장 저장
    if st.session_state.selected_words:
        save_current_sentence()
    
    # 다음 문장으로 이동
    if st.session_state.current_sentence_idx < len(st.session_state.sentences) - 1:
        st.session_state.current_sentence_idx += 1
        reset_current_sentence()
    else:
        st.info("마지막 문장입니다.")


def move_to_previous_sentence():
    """이전 문장으로 이동"""
    if st.session_state.current_sentence_idx > 0:
        # 현재 문장 저장
        if st.session_state.selected_words:
            save_current_sentence()
        
        st.session_state.current_sentence_idx -= 1
        reset_current_sentence()
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
    
    # 제목
    st.title("🌐 Word-for-Word Translation")
    st.markdown("---")
    
    # 사이드바: 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 언어 선택
        translation_direction = st.selectbox(
            "번역 방향",
            ["한국어 → 영어", "영어 → 한국어"],
            index=0 if st.session_state.source_lang == 'ko' else 1
        )
        
        if translation_direction == "한국어 → 영어":
            st.session_state.source_lang = 'ko'
            st.session_state.target_lang = 'en'
        else:
            st.session_state.source_lang = 'en'
            st.session_state.target_lang = 'ko'
        
        # DeepL API 키 입력
        st.subheader("DeepL API 키")
        api_key_input = st.text_input(
            "API 키",
            value=st.session_state.deepl_api_key,
            type="password",
            help="DeepL API 키를 입력하세요. .env 파일에서도 로드됩니다."
        )
        
        if api_key_input and api_key_input != st.session_state.deepl_api_key:
            if initialize_translator(api_key_input):
                st.success("API 키가 설정되었습니다.")
        
        if st.session_state.translator:
            st.success("✅ 번역기 준비됨")
        else:
            st.warning("⚠️ API 키를 설정하세요")
        
        st.markdown("---")
        
        # 진행 상황
        if st.session_state.sentences:
            st.subheader("📊 진행 상황")
            total = len(st.session_state.sentences)
            current = st.session_state.current_sentence_idx + 1
            st.progress(current / total if total > 0 else 0)
            st.caption(f"{current} / {total} 문장")
            st.caption(f"완료: {len(st.session_state.translation_history)} 문장")
        
        st.markdown("---")
        
        # 텍스트 입력
        st.header("📝 텍스트 입력")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "텍스트 파일 업로드",
            type=['txt'],
            help="한국어 또는 영어 텍스트 파일을 업로드하세요."
        )
        
        if uploaded_file is not None:
            text = uploaded_file.read().decode('utf-8')
            if text != st.session_state.full_text:
                process_text_input(text)
        
        # 텍스트 붙여넣기
        text_input = st.text_area(
            "또는 텍스트를 붙여넣으세요",
            height=100,
            help="텍스트를 직접 입력하거나 붙여넣으세요."
        )
        
        if st.button("텍스트 처리", type="primary", use_container_width=True):
            if text_input:
                process_text_input(text_input)
            else:
                st.warning("텍스트를 입력하세요.")
    
    # 메인 영역
    
    # 번역 영역
    if st.session_state.sentences:
        st.markdown("---")
        st.header("🔄 번역")
        
        # 현재 문장 정보
        current_sentence = st.session_state.sentences[st.session_state.current_sentence_idx]
        st.caption(f"문장 {st.session_state.current_sentence_idx + 1} / {len(st.session_state.sentences)}")
        
        # 오른쪽 메인 영역: 번역과 번역 완료 탭
        tab1, tab2 = st.tabs(["🔄 번역", "✅ 번역 완료"])
        
        with tab1:
            # 번역 탭 안에 원문과 번역을 나란히 표시
            left_col, right_col = st.columns([1, 1])
            
            with left_col:
                st.subheader("📖 원문")
                
                # 선택된 어절들 표시
                if st.session_state.selected_words:
                    # 선택된 단어들을 순서대로 정렬
                    sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                    selected_text = ' '.join([w[1] for w in sorted_words])
                    st.text_area(
                        "선택된 텍스트",
                        value=selected_text,
                        height=100,
                        disabled=True,
                        key=f"selected_text_display_{st.session_state.current_sentence_idx}_{len(st.session_state.selected_words)}"
                    )
                
                # 어절 버튼들 (토글)
                st.markdown("**어절을 클릭하여 선택/해제하세요:**")
                
                if st.session_state.current_words:
                    # 선택된 단어 인덱스 리스트
                    selected_indices = [w[0] for w in st.session_state.selected_words]
                    
                    # 버튼을 그리드로 배치
                    cols_per_row = 3
                    
                    # 모든 어절을 버튼으로 표시 (선택된 것은 강조)
                    # 버튼 렌더링
                    for row_start in range(0, len(st.session_state.current_words), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col_idx, col in enumerate(cols):
                            word_idx = row_start + col_idx
                            if word_idx < len(st.session_state.current_words):
                                word = st.session_state.current_words[word_idx]
                                button_key = f"word_btn_{st.session_state.current_sentence_idx}_{word_idx}"
                                
                                # 선택된 단어는 primary 타입으로 표시
                                is_selected = word_idx in selected_indices
                                button_clicked = col.button(
                                    word,
                                    key=button_key,
                                    use_container_width=True,
                                    type="primary" if is_selected else "secondary"
                                )
                                if button_clicked:
                                    handle_word_click(word_idx)
                                    st.rerun()
                else:
                    st.info("어절이 없습니다.")
            
            with right_col:
                st.subheader("🌍 번역")
                
                # 번역 결과 표시
                # 선택된 단어가 있으면 실시간으로 번역 표시
                if st.session_state.selected_words:
                    # 선택된 단어들을 순서대로 정렬
                    sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                    accumulated_text = ' '.join([w[1] for w in sorted_words])
                    
                    # 번역 수행 (번역기가 있고 텍스트가 있을 때만)
                    if st.session_state.translator and accumulated_text:
                        try:
                            translated = st.session_state.translator.translate(
                                accumulated_text,
                                st.session_state.source_lang,
                                st.session_state.target_lang
                            )
                            st.session_state.current_translation = translated
                            st.text_area(
                                "번역 결과",
                                value=translated,
                                height=100,
                                disabled=True,
                                key=f"translation_display_{st.session_state.current_sentence_idx}_{len(st.session_state.selected_words)}"
                            )
                        except translation.TranslationError as e:
                            st.error(str(e))
                            if st.session_state.current_translation:
                                st.text_area(
                                    "번역 결과",
                                    value=st.session_state.current_translation,
                                    height=100,
                                    disabled=True,
                                    key=f"translation_display_error_{st.session_state.current_sentence_idx}_{len(st.session_state.selected_words)}"
                                )
                    elif st.session_state.current_translation:
                        # 번역기가 없어도 이전 번역 결과 표시
                        st.text_area(
                            "번역 결과",
                            value=st.session_state.current_translation,
                            height=100,
                            disabled=True,
                            key=f"translation_display_prev_{st.session_state.current_sentence_idx}_{len(st.session_state.selected_words)}"
                        )
                    else:
                        st.info("어절을 클릭하면 번역이 표시됩니다.")
                elif st.session_state.current_translation:
                    st.text_area(
                        "번역 결과",
                        value=st.session_state.current_translation,
                        height=100,
                        disabled=True,
                        key=f"translation_display_final_{st.session_state.current_sentence_idx}_{len(st.session_state.selected_words)}"
                    )
                else:
                    st.info("어절을 클릭하면 번역이 표시됩니다.")
                
                # 번역 버튼 (수동 번역)
                if st.session_state.selected_words and st.session_state.translator:
                    # 선택된 단어들을 순서대로 정렬
                    sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                    accumulated_text = ' '.join([w[1] for w in sorted_words])
                    if st.button("🔄 번역 새로고침", use_container_width=True):
                        try:
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
            st.subheader("✅ 번역 완료")
            
            # 번역된 내용 표시
            if st.session_state.translation_history:
                st.write(f"**번역 완료된 문장 수: {len(st.session_state.translation_history)}**")
                st.markdown("---")
                
                # 번역된 내용을 표시
                translation_text = ""
                for idx, (original, translated) in enumerate(st.session_state.translation_history, 1):
                    translation_text += f"{idx}. {original} | {translated}\n"
                
                st.text_area(
                    "번역 완료 내용",
                    value=translation_text,
                    height=400,
                    disabled=True,
                    key="completed_translations_display"
                )
                
                # 전체 번역 저장 버튼
                if st.button("💾 전체 번역 저장", use_container_width=True, type="primary"):
                    try:
                        filepath = storage.save_translation(st.session_state.translation_history)
                        st.success(f"번역이 저장되었습니다: {filepath}")
                    except Exception as e:
                        st.error(f"저장 중 오류: {str(e)}")
            else:
                st.info("아직 번역 완료된 문장이 없습니다. 번역 탭에서 작업을 진행하세요.")
        
        # 네비게이션 버튼
        st.markdown("---")
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        
        with nav_col1:
            if st.button("◀ 이전 문장", use_container_width=True):
                move_to_previous_sentence()
                st.rerun()
        
        with nav_col2:
            if st.button("다음 문장 ▶", use_container_width=True, type="primary"):
                move_to_next_sentence()
                st.rerun()
        
        with nav_col3:
            if st.button("🔄 현재 문장 리셋", use_container_width=True):
                reset_current_sentence()
                st.rerun()
    
    else:
        # 안내 메시지
        st.info("👆 위에서 텍스트 파일을 업로드하거나 텍스트를 입력하세요.")


if __name__ == "__main__":
    main()
