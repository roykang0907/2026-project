# CLAUDE.md — aiteacherguard 개발 컨텍스트

> 이 파일은 개발 레포에 두면 Claude Code가 매 세션 자동으로 읽는 컨텍스트다.
> **이전 설계 대화를 그대로 이어받아 곧바로 개발을 진행한다.** 상세 설계는 `개발레포_CLAUDE_핸드오프.md` 참조.

---

## 프로젝트 한 줄

**aiteacherguard** — 학부모 악성 민원으로부터 **교사를 보호**하고 그 결과 **학생 학습권을 회복**하는 **로컬 추론 기반 3단계 AI 시스템**. (공모전 출품작)

핵심 메시지: *"교사를 보호함으로써 학생의 학습권을 회복한다."*

---

## ✅ 확정된 기술 결정 (변경 금지, 바꾸려면 사용자 확인)

```
1단계 분류  → KoBERT (인코더) ............ AI Hub 감성 대화 말뭉치 → 정상/주의/위험 3클래스
2단계 순화  → Qwen2.5-14B (디코더) ....... AI Hub 공적 말하기 실습·평가 데이터 + 합성데이터, QLoRA
              ↳ Ollama 서빙 (`ollama pull qwen2.5:14b`), 대안 Llama 3.x
3단계 답변  → 2단계 모델 + RAG(pgvector)
추론 런타임 → Ollama (localhost:11434)
```

- **모델은 2개.** KoBERT는 인코더라 **분류만** 가능(생성 불가). 순화(rewrite)는 생성형 디코더 LLM이 별도로 담당.
- 파인튜닝 흐름: LoRA 병합 → GGUF 변환 → `ollama create`.

### 스택
- 백엔드: FastAPI(Python 3.11) + PostgreSQL + pgvector + WebSocket
- 프론트: Vite + React + TS + Tailwind + shadcn/ui + Zustand + React Query + Tiptap
- ML: transformers + PEFT + TRL (+ Unsloth), QLoRA 4-bit (r=16, alpha=32)
- 1단계: `skt/kobert-base-v1` + `kobert_tokenizer`

### 절대 원칙 (발표 방어 논리 = 변경 금지)
1. 순화 뷰 기본 + **원본 항상 열람 가능** (은폐 아님)
2. 긴급 분기 — 안전·법적 사안(학폭·아동학대·자해·고소)은 룰로 즉시 위험 상단
3. **로컬 추론만** (외부 API 금지 — 개인정보)
4. 메타데이터(반복성·강도·원어조) 분리 저장
5. "AI 제안, 최종 책임은 교사" disclaimer 고정
6. 학습 데이터에 실제 학부모 발화 없음(가상 시나리오 자체 작성)

---

## 📍 현재 상태 (이어서 진행할 지점)

- 연구·통계·설계 **완료**. 모델·런타임 **확정**. **코드는 아직 0.**
- AI Hub 데이터셋 **신청 단계** (사용자가 진행 중 / 승인 1~3일 대기).

## ▶ 다음 작업 (이 순서대로)

1. **STEP 1 — 레포 골격**: `ml/ backend/ frontend/ data/ docs/` + `.gitignore`(모델·대용량 제외), Python 3.11/Node 20, Ollama 설치
2. **STEP 2 — KoBERT 1단계** ⭐ 첫 코드:
   - 정상/주의/위험 라벨 매핑 + 긴급 키워드 룰 사전
   - **더미 데이터로 도는 학습→예측 파이프라인 골격 먼저** (AI Hub 승인 대기용)
   - 승인 후 실데이터 파인튜닝 → Macro-F1 평가 (위험→정상 오분류 최소화가 최우선)
3. **STEP 3 — 2단계 순화 LLM + RAG**: 합성데이터 1000건 생성 → Qwen2.5 QLoRA → GGUF → Ollama → pgvector RAG
4. **STEP 4 — 백엔드**: FastAPI 5 엔드포인트 + 린터 룰 + docker-compose
5. **STEP 5 — 프론트**: 비동기 대시보드(순화 카드/원본 토글/우선순위 큐) + Tiptap 실시간 빨간줄
6. **STEP 6 — 통합·시연·발표**

### FastAPI 엔드포인트 (4단계 목표)
- `POST /api/complaints/ingest` · `GET /api/complaints` · `GET /api/complaints/{id}`
- `POST /api/draft/suggest` (RAG+LLM) · `POST /api/draft/validate` (린터)

---

## 작업 규칙

- 사용자가 시킨 작업은 **commit → main push까지 자동 반영** (사용자는 GitHub Desktop에서 Pull만).
- 윈도우↔맥 GitHub Desktop 동기화 환경. 무거운 학습 산출물은 git 제외, 코드/노트북 골격만.
- 연구 근거·통계·논문·그래프 원본은 **자료 레포 `2026-project`**에 있음 (이 레포로 복사 X, 필요한 CSV만).

---

## 역할 분담

| 사용자만 | Claude |
|---|---|
| AI Hub 신청, Ollama 설치, 맥북 학습 실행, GitHub Desktop Pull | 레포 골격·전체 코드·스크립트·노트북·문서·린터 룰·데모 |
