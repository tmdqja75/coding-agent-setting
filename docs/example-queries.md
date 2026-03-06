# Example Queries — Claude Code Setup Agent

Each example shows a full conversation flow via `POST /chat`.
The agent asks up to 3 follow-up questions (in Korean) before building the zip.

---

## Request format

```json
{
  "thread_id": "<unique-session-id>",
  "message": "<user message>"
}
```

---

## 1. Next.js / React Frontend

**Turn 1 — User opens conversation**

```json
{
  "thread_id": "thread-nextjs-001",
  "message": "Next.js 15 App Router로 SaaS 대시보드를 만들고 있어요. TypeScript, Tailwind CSS, Prisma ORM을 씁니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "주요 워크플로우가 무엇인가요? (예: 컴포넌트 개발, DB 마이그레이션, 배포 자동화 등)" }
```

**Turn 2 — User answers**

```json
{
  "thread_id": "thread-nextjs-001",
  "message": "컴포넌트 작성, Prisma 스키마 변경, Vercel 배포가 주요 작업입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "테스트 도구나 코드 품질 도구(예: Vitest, ESLint, Storybook)를 사용하시나요?" }
```

**Turn 3 — User answers**

```json
{
  "thread_id": "thread-nextjs-001",
  "message": "Vitest로 단위 테스트하고, ESLint + Prettier 씁니다. Storybook도 씁니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 2. Python Data Science / ML

**Turn 1**

```json
{
  "thread_id": "thread-ds-001",
  "message": "Python 데이터 분석 프로젝트입니다. pandas, scikit-learn, Jupyter Notebook을 주로 씁니다. 금융 데이터 시각화와 ML 모델 학습이 주요 작업입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "모델 실험 추적이나 데이터 버전 관리 도구(예: MLflow, DVC, W&B)를 사용하시나요?" }
```

**Turn 2**

```json
{
  "thread_id": "thread-ds-001",
  "message": "MLflow로 실험을 추적하고 있고, 데이터는 S3에 저장합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 3. DevOps / Infrastructure (Terraform + Kubernetes)

**Turn 1**

```json
{
  "thread_id": "thread-devops-001",
  "message": "AWS 인프라를 Terraform으로 관리하고, EKS 클러스터에 서비스를 배포합니다. CI/CD는 GitHub Actions입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "모니터링이나 로그 관리 도구(예: Datadog, Prometheus, CloudWatch)를 사용하시나요?" }
```

**Turn 2**

```json
{
  "thread_id": "thread-devops-001",
  "message": "Datadog으로 메트릭과 로그를 관리합니다. 알림은 PagerDuty와 연결되어 있어요."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 4. FastAPI Python Backend

**Turn 1**

```json
{
  "thread_id": "thread-fastapi-001",
  "message": "FastAPI로 REST API 서버를 만들고 있어요. PostgreSQL, SQLAlchemy, Alembic을 씁니다. Docker로 컨테이너화합니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "API 테스트나 문서화 방식이 어떻게 되나요? (예: pytest, Postman, OpenAPI 자동 생성 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-fastapi-001",
  "message": "pytest로 테스트하고, FastAPI의 자동 OpenAPI 문서를 활용합니다. httpx로 통합 테스트도 합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 5. React Native Mobile App

**Turn 1**

```json
{
  "thread_id": "thread-rn-001",
  "message": "React Native + Expo로 iOS/Android 앱을 개발합니다. 상태 관리는 Zustand, 백엔드는 Supabase입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "주요 개발 워크플로우가 무엇인가요? (예: 기기 테스트, 스토어 제출, 디자인-개발 핸드오프 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-rn-001",
  "message": "Expo Go로 빠르게 테스트하고, EAS Build로 빌드합니다. Figma 디자인을 자주 참고합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 6. Monorepo — Full-stack SaaS (Turborepo)

**Turn 1**

```json
{
  "thread_id": "thread-monorepo-001",
  "message": "Turborepo 모노레포 구조로 Next.js 프론트엔드, NestJS 백엔드, 공유 패키지를 관리합니다. pnpm workspaces를 씁니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "팀 규모와 주요 협업 방식이 어떻게 되나요? (예: PR 리뷰, 코드 소유자, 브랜치 전략 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-monorepo-001",
  "message": "5명 팀이고, GitHub Flow를 씁니다. CODEOWNERS로 각 패키지 소유자를 지정했습니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "CI/CD나 배포 파이프라인은 어떻게 구성되어 있나요?" }
```

**Turn 3**

```json
{
  "thread_id": "thread-monorepo-001",
  "message": "GitHub Actions로 빌드/테스트하고, 프론트는 Vercel, 백엔드는 Railway에 배포합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 7. Game Development (Unity / C#)

**Turn 1**

```json
{
  "thread_id": "thread-unity-001",
  "message": "Unity 6으로 2D 모바일 게임을 만들고 있어요. C# 스크립트, Addressables, Firebase Analytics를 씁니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "주요 반복 작업이 무엇인가요? (예: 씬 빌드, 에셋 번들 관리, 플레이테스트 피드백 처리 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-unity-001",
  "message": "Addressables 빌드, 플레이어 데이터 분석, 버그 리포트 처리가 반복적입니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 8. Market Research Analyst

**Turn 1**

```json
{
  "thread_id": "thread-market-001",
  "message": "시장 조사 업무를 합니다. 경쟁사 분석, 소비자 트렌드 리서치, 보고서 작성이 주요 업무예요. 주로 웹 검색, 뉴스 수집, Excel 데이터 정리를 합니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "보고서 작성 시 주로 어떤 형식을 사용하시나요? (예: Word/Google Docs 문서, PowerPoint 슬라이드, Notion 페이지 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-market-001",
  "message": "Notion에 정리하고, 최종 보고서는 PowerPoint로 만듭니다. 데이터는 Google Sheets로 관리해요."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 9. Academic Researcher / Paper Writing

**Turn 1**

```json
{
  "thread_id": "thread-research-001",
  "message": "논문 작성과 문헌 조사를 합니다. 참고문헌 관리는 Zotero, 작성은 LaTeX입니다. 주요 작업은 논문 검색, 요약, 인용 정리, 초안 작성입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "어떤 분야의 연구를 하시나요? (예: 자연과학, 사회과학, 공학, 의학 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-research-001",
  "message": "컴퓨터 과학 분야이고, arXiv와 Google Scholar에서 주로 논문을 찾습니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 10. Content Creator / Writer

**Turn 1**

```json
{
  "thread_id": "thread-content-001",
  "message": "블로그와 뉴스레터 콘텐츠를 제작합니다. 아이디어 발굴, 초안 작성, SEO 최적화, 소셜미디어 배포가 주요 업무예요."
}
```

**Agent response**
```json
{ "type": "question", "text": "주로 어떤 플랫폼에 콘텐츠를 발행하시나요? (예: Substack, Notion, WordPress, Medium 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-content-001",
  "message": "Substack으로 뉴스레터를 보내고, 블로그는 WordPress입니다. X(트위터)와 LinkedIn에도 요약본을 올립니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 11. Finance / Investment Analysis

**Turn 1**

```json
{
  "thread_id": "thread-finance-001",
  "message": "주식 및 ETF 투자 분석을 합니다. 재무제표 분석, 실적 발표 요약, 포트폴리오 수익률 추적이 주요 업무입니다. Excel과 Python을 씁니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "데이터 출처가 어떻게 되나요? (예: Bloomberg, Yahoo Finance, DART 공시, 직접 크롤링 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-finance-001",
  "message": "Yahoo Finance API와 DART 공시 데이터를 주로 씁니다. Python으로 자동 수집하고 Excel로 정리합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 12. Legal / Contract Review

**Turn 1**

```json
{
  "thread_id": "thread-legal-001",
  "message": "계약서 검토와 법률 문서 작성을 합니다. 주요 업무는 계약 조항 분석, 리스크 정리, 표준 계약서 초안 작성입니다. 주로 Word 문서와 PDF를 다룹니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "계약서 검토 시 주로 어떤 유형의 문서를 다루시나요? (예: NDA, 용역 계약, 투자 계약, 임대차 계약 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-legal-001",
  "message": "주로 NDA와 소프트웨어 용역 계약서를 검토합니다. 영문 계약서도 자주 다룹니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 13. HR / Recruiting

**Turn 1**

```json
{
  "thread_id": "thread-hr-001",
  "message": "채용 담당자입니다. 이력서 검토, 직무 기술서(JD) 작성, 면접 질문 준비, 합격자 온보딩 자료 정리가 주요 업무입니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "채용 관리 도구나 ATS(지원자 추적 시스템)를 사용하시나요? (예: Greenhouse, Lever, Notion, Google Sheets 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-hr-001",
  "message": "Notion으로 채용 파이프라인을 관리하고, Google Forms로 지원서를 받습니다. Slack으로 팀 협업합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 14. Product Manager

**Turn 1**

```json
{
  "thread_id": "thread-pm-001",
  "message": "프로덕트 매니저입니다. 기능 기획, PRD 작성, 스프린트 관리, 사용자 인터뷰 정리가 주요 업무입니다. Jira, Confluence, Figma를 씁니다."
}
```

**Agent response**
```json
{ "type": "question", "text": "데이터 기반 의사결정을 위해 어떤 분석 도구를 사용하시나요? (예: Amplitude, Mixpanel, Google Analytics, Looker 등)" }
```

**Turn 2**

```json
{
  "thread_id": "thread-pm-001",
  "message": "Amplitude로 사용자 행동 분석하고, SQL로 직접 데이터를 뽑기도 합니다."
}
```

**Agent response**
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

## 15. Edge Cases

### 15a. Very short / vague initial message

**Turn 1**

```json
{
  "thread_id": "thread-vague-001",
  "message": "웹 개발이요."
}
```

**Agent response** — will ask for specifics
```json
{ "type": "question", "text": "어떤 종류의 웹 서비스를 개발하시나요? 프론트엔드, 백엔드, 또는 풀스택인지와 주요 기술 스택을 알려주세요." }
```

---

### 15b. Non-Korean initial message (English)

**Turn 1**

```json
{
  "thread_id": "thread-english-001",
  "message": "I'm building a Django REST API with PostgreSQL. I use pytest for testing and deploy to Heroku."
}
```

**Agent response** — agent responds in Korean regardless
```json
{ "type": "question", "text": "주요 개발 워크플로우가 무엇인가요? (예: API 테스트, DB 마이그레이션, 배포 자동화 등)" }
```

---

### 15c. Highly detailed first message (agent skips questions, builds immediately)

**Turn 1**

```json
{
  "thread_id": "thread-detailed-001",
  "message": "Go 백엔드 API 서버입니다. Gin 프레임워크, PostgreSQL, Redis 캐시를 씁니다. 주요 작업은 API 엔드포인트 작성, DB 스키마 마이그레이션(golang-migrate), Redis 캐시 전략 구현입니다. 테스트는 testify로 하고, Docker Compose로 로컬 개발, GitHub Actions + GCP Cloud Run으로 배포합니다."
}
```

**Agent response** — enough context, proceeds directly
```json
{ "type": "ready", "text": "설정 파일을 생성했습니다." }
```

---

### 15d. Download after completion

Once the agent returns `"type": "ready"`, fetch the generated zip:

```bash
curl -OJ http://localhost:8000/download/thread-nextjs-001
# saves: claude-code-setup.zip
```
