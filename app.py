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
    """현재 문장 상태 초기화 (저장된 상태가 있으면 복원, 없으면 초기화)"""
    restore_sentence_state(st.session_state.current_sentence_idx)


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


def save_current_sentence():
    """현재 문장 번역 저장"""
    if not st.session_state.sentences:
        return
    
    current_sentence = st.session_state.sentences[st.session_state.current_sentence_idx]
    translation_text = st.session_state.current_translation
    sentence_idx = st.session_state.current_sentence_idx
    
    if current_sentence and translation_text:
        # 문장 인덱스를 키로 사용하여 저장 (중복 방지 및 업데이트)
        if sentence_idx in st.session_state.translation_history:
            st.session_state.translation_history[sentence_idx] = (current_sentence, translation_text)
            st.success("번역이 업데이트되었습니다.")
        else:
            st.session_state.translation_history[sentence_idx] = (current_sentence, translation_text)
            st.success("번역이 저장되었습니다.")


def move_to_next_sentence():
    """다음 문장으로 이동"""
    if not st.session_state.sentences:
        return
    
    # 현재 문장의 상태 저장 (선택된 단어, 번역 결과 등)
    save_current_sentence_state()
    
    # 현재 문장 저장 (번역 결과가 있으면 저장)
    if st.session_state.current_translation:
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
        
        # 현재 문장 저장 (번역 결과가 있으면 저장)
        if st.session_state.current_translation:
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
                # handle_word_click에서 이미 번역을 수행했으므로 여기서는 표시만
                if st.session_state.current_translation:
                    # 달라진 단어를 빨간색으로 표시
                    highlighted = highlight_different_words(
                        st.session_state.current_translation,
                        st.session_state.previous_translation
                    )
                    st.markdown("**번역 결과:**")
                    st.markdown(f'<div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; min-height: 100px; background-color: #f9f9f9;">{highlighted}</div>', unsafe_allow_html=True)
                elif st.session_state.selected_words:
                    st.info("어절을 클릭하면 번역이 표시됩니다.")
                else:
                    st.info("어절을 클릭하면 번역이 표시됩니다.")
                
                # 번역 버튼 (수동 번역)
                if st.session_state.selected_words and st.session_state.translator:
                    # 선택된 단어들을 순서대로 정렬
                    sorted_words = sorted(st.session_state.selected_words, key=lambda x: x[0])
                    accumulated_text = ' '.join([w[1] for w in sorted_words])
                    if st.button("🔄 번역 새로고침", use_container_width=True):
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
            st.subheader("✅ 번역 완료")
            
            # 번역된 내용 표시
            if st.session_state.translation_history:
                st.write(f"**번역 완료된 문장 수: {len(st.session_state.translation_history)}**")
                st.markdown("---")
                
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
                    
                    # 디버깅: 생성된 텍스트 확인 (주석 처리)
                    # st.write(f"🔍 생성된 번역 텍스트 길이: {len(translation_text)}, 줄 수: {len(translation_text.split(chr(10)))}")
                    # st.write(f"🔍 생성된 번역 텍스트 내용 (repr): {repr(translation_text)}")
                    # st.write(f"🔍 생성된 번역 텍스트 내용 (실제): {translation_text}")
                else:
                    # 리스트 형식인 경우 (호환성)
                    for idx, item in enumerate(st.session_state.translation_history, 1):
                        if isinstance(item, tuple) and len(item) == 2:
                            original, translated = item
                            translation_text += f"{idx}. {original} | {translated}\n"
                        else:
                            translation_text += f"{idx}. [오류: 잘못된 데이터 형식]\n"
                
                # st.text_area는 여러 줄 표시에 문제가 있어 st.markdown으로 변경
                # HTML 이스케이프 처리
                import html
                translation_text_escaped = html.escape(translation_text)
                # 줄바꿈을 HTML <br>로 변환하여 표시
                translation_text_html = translation_text_escaped.replace('\n', '<br>')
                st.markdown(
                    f'<div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; min-height: 400px; background-color: #f9f9f9; white-space: pre-wrap; font-family: monospace;">{translation_text_html}</div>',
                    unsafe_allow_html=True
                )
                
                # 전체 번역 저장 버튼
                if st.button("💾 전체 번역 저장", use_container_width=True, type="primary"):
                    try:
                        # 딕셔너리를 리스트로 변환 (storage 함수 호환성)
                        translation_list = list(st.session_state.translation_history.values())
                        filepath = storage.save_translation(translation_list)
                        st.success(f"번역이 저장되었습니다: {filepath}")
                    except Exception as e:
                        st.error(f"저장 중 오류: {str(e)}")
            else:
                st.info("아직 번역 완료된 문장이 없습니다. 번역 탭에서 작업을 진행하세요.")
        
        # 네비게이션 버튼
        st.markdown("---")
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
        
        # 현재 문장 인덱스와 전체 문장 수
        current_idx = st.session_state.current_sentence_idx
        total_sentences = len(st.session_state.sentences)
        is_first_sentence = current_idx == 0
        is_last_sentence = current_idx == total_sentences - 1
        
        with nav_col1:
            if st.button("◀ 이전 문장", use_container_width=True, disabled=is_first_sentence):
                move_to_previous_sentence()
                st.rerun()
        
        with nav_col2:
            # 마지막 문장인 경우 "저장" 버튼, 그 외에는 "저장 및 다음 문장" 버튼
            if is_last_sentence:
                button_text = "💾 저장"
            else:
                button_text = "💾 저장 및 다음 문장"
            
            if st.button(button_text, use_container_width=True, type="primary"):
                if is_last_sentence:
                    # 마지막 문장: 저장만 수행
                    if st.session_state.current_translation:
                        save_current_sentence()
                else:
                    # 그 외: 저장 후 다음 문장으로 이동
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
