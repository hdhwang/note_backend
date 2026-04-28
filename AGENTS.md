# 🤖 AI Agents & Skills Integration Plan

이 문서는 `note_backend` 프로젝트에 향후 도입하거나 연동할 수 있는 AI 에이전트 및 모듈화된 스킬(Skill)들의 기획안을 다룹니다. Django REST Framework 환경에 맞춰 비동기 태스크(Celery 등)나 외부 LLM API(OpenAI, Anthropic 등)와 결합하여 고도화할 수 있습니다.

---

## 1. 📝 Note Processing Agent (노트 프로세싱 에이전트)

기존 `Note` 모델의 데이터를 활용하여 사용자의 기록을 지능적으로 관리합니다.

- **Auto-Summarization Skill (자동 요약 스킬)**
  - **기능**: 사용자가 긴 내용의 노트를 작성(POST/PUT)할 때, 백그라운드에서 내용을 분석하여 짧은 요약본을 생성하고 `Note` 모델의 새로운 필드(예: `summary`)에 자동 저장.
  - **활용 API**: LLM Text Completion API.
  
- **Auto-Tagging & Categorization Skill (자동 태깅 및 분류 스킬)**
  - **기능**: 노트 본문의 맥락을 파악하여 자동으로 관련된 태그(키워드)를 추출하고 카테고리를 분류. 이를 통해 검색(Search) 효율성을 극대화.

---

## 2. 🛡️ Security & Anomaly Detection Agent (보안 및 이상 탐지 에이전트)

강력한 `AuditLog` 시스템과 연계하여 시스템의 보안을 강화합니다.

- **Suspicious Activity Monitoring Skill (의심 활동 모니터링 스킬)**
  - **기능**: `AuditLog` 데이터와 실시간 갱신되는 `last_login` 정보를 분석하여 비정상적인 패턴(예: 짧은 시간 내 다수의 로그인 실패, 평소와 다른 IP 대역에서의 대량 데이터 조회 및 삭제)을 탐지.
  - **액션**: 이상 탐지 시 관리자에게 알림(`mail_helper.py` 활용) 발송.

---

## 3. 📊 Financial Data Assistant (재무 데이터 어시스턴트)

`BankAccount` 및 `GuestBook`(축의금/방명록) 데이터를 기반으로 인사이트를 제공합니다.

- **GuestBook Analytics Skill (방명록 분석 스킬)**
  - **기능**: 결혼식 방명록에 기록된 금액(`amount`), 장소(`area`), 참석 여부(`attend`) 등을 분석하여, 평균 축의금 액수, 그룹별/지역별 통계 레포트를 자연어 형태로 제공.
  
- **Account Usage Report Skill (계좌 활용 리포트 스킬)**
  - **기능**: 등록된 은행 계좌와 설명(`description`) 데이터를 바탕으로 사용자의 자산 풀을 정리하고, 사용자별 데이터가 격리된 대시보드 API(`DashboardStatsAPI`)와 연계하여 맞춤형 요약 브리핑 생성.

---

## 4. 🔍 Semantic Search Agent (시맨틱 검색 에이전트)

단순 문자열 매칭(icontains)을 넘어선 의미 기반 검색을 제공합니다.

- **Vector Database Integration Skill (벡터 DB 검색 스킬)**
  - **기능**: 노트 내용, 시리얼 제품 설명 등을 임베딩(Embedding)하여 Vector DB(예: Pinecone, Milvus, pgvector)에 저장.
  - **활용**: 사용자가 "작년에 샀던 영상 편집 프로그램 키가 뭐지?"라고 자연어로 검색하면 의미를 분석하여 관련 `Serial` 데이터를 반환.

---

## 5. 🔮 Lotto Analysis Skill (로또 분석 스킬)

현재 랜덤으로 번호를 생성하는 `LottoAPI`를 고도화합니다.

- **Statistical Number Generation (통계 기반 번호 생성)**
  - **기능**: 외부의 역대 로또 당첨 번호 데이터를 수집하여 통계적 확률(출현 빈도, 미출현 번호 등)을 기반으로 추천 번호를 생성 및 분석 리포트 제공.

---

## 🚀 도입 가이드라인

1. **LLM 연동 모듈 신설**: `utils/llm_helper.py` 등을 생성하여 외부 API 호출 로직 중앙화.
2. **비동기 처리**: AI 분석은 시간이 소요되므로 Celery + Redis/RabbitMQ를 도입하여 비동기 Task로 처리하는 것을 권장.
3. **암호화 데이터 처리 주의**: `Note`나 `Serial`의 데이터는 AES 암호화되어 있으므로, AI 에이전트에게 컨텍스트를 제공하기 전 서버 측에서 복호화 과정을 거쳐야 하며, 처리 후 외부 로그에 민감 데이터가 남지 않도록 주의 필요.
