# AI4RM 프로젝트 Copilot 설정 가이드

## 📁 프롬프트 파일 구조

```
.github/copilot/
├── prompts/                     # 전문가별 프롬프트
│   ├── medical-expert.json     # 의료 데이터 전문가
│   ├── security-specialist.json # 보안 전문가  
│   ├── vault-integration.json   # Vault 통합 전문가
│   ├── devops-engineer.json     # DevOps 엔지니어
│   └── compliance-auditor.json  # 컴플라이언스 감사관
├── contexts/                    # 프로젝트 컨텍스트
│   └── ai4rm-core.json         # 핵심 프로젝트 정보
├── AI_CODING_GUIDELINES.md     # 개발 지침 (메인)
└── README.md                    # 이 파일
```

## 🎯 프롬프트 사용법

### VS Code 설정 추가
`.vscode/settings.json`에 다음 설정을 추가하세요:

```json
{
    "python.envFile": "${workspaceFolder}/.env",
    "github.copilot.chat.customPrompts": {
        "medical": {
            "path": "${workspaceFolder}/.github/copilot/prompts/medical-expert.json"
        },
        "security": {
            "path": "${workspaceFolder}/.github/copilot/prompts/security-specialist.json"
        },
        "vault": {
            "path": "${workspaceFolder}/.github/copilot/prompts/vault-integration.json"
        },
        "devops": {
            "path": "${workspaceFolder}/.github/copilot/prompts/devops-engineer.json"
        },
        "compliance": {
            "path": "${workspaceFolder}/.github/copilot/prompts/compliance-auditor.json"
        }
    }
}
```

### 프롬프트 선택 방법

#### 1. 채팅 사이드바에서 선택
- **단축키**: `Ctrl+Shift+I` (채팅 사이드바 열기)
- **프롬프트 선택**: 채팅 입력창 상단의 **⚙️ 설정 버튼** 클릭
- **드롭다운**: 사용 가능한 프롬프트 목록에서 선택

#### 2. @ 기호로 직접 호출
```
@medical 환자 데이터 처리 함수 작성
@security 보안 취약점 검토
@vault Vault 클라이언트 연동
@devops Docker 설정 생성
@compliance GDPR 컴플라이언스 검토
```

#### 3. 인라인 채팅에서 사용
- **단축키**: `Ctrl+I` (인라인 채팅)
- **프롬프트**: `@프롬프트명 요청사항` 입력

#### 4. 명령 팔레트 활용
- **단축키**: `Ctrl+Shift+P`
- **명령어**: "Copilot: Select Prompt" 검색

### 채팅에서 프롬프트 활용

#### 1. 의료 데이터 개발
```
@medical
환자 ID를 SHA-256으로 해싱하되 GDPR Article 4(5) 가명처리 요구사항을 만족하는 함수를 작성해줘
```

#### 2. 보안 검토
```  
@security
이 코드에서 OWASP Top 10 취약점을 검토하고 수정 방안을 제시해줘
```

#### 3. Vault 통합
```
@vault
데이터베이스 크리덴셜을 Vault에서 동적으로 가져오고 자동 갱신하는 코드를 작성해줘
```

#### 4. DevOps 작업
```
@devops
AI4RM 서비스들을 위한 보안 강화된 Docker Compose 설정을 만들어줘
```

#### 5. 컴플라이언스 검토
```
@compliance
이 개인정보 처리 로직이 GDPR Article 25 (데이터 보호 내재화) 요구사항을 준수하는지 검토해줘
```

## 🔧 프롬프트 커스터마이징

### 새 프롬프트 추가
1. `.github/copilot/prompts/` 폴더에 새 JSON 파일 생성
2. 프롬프트 구조에 맞춰 내용 작성
3. VS Code 설정에 새 프롬프트 참조 추가

### 기존 프롬프트 수정
1. 해당 JSON 파일 편집
2. VS Code 재시작으로 변경사항 적용

## 📋 프롬프트별 사용 시나리오

### 🏥 Medical Expert
- 환자 데이터 익명화/가명처리
- K-anonymity, L-diversity 구현
- 의료 용어 및 코드 체계 작업
- GDPR/HIPAA 준수 데이터 처리

### 🔒 Security Specialist  
- 보안 취약점 검토 및 수정
- 암호화/해싱 구현
- 인증/권한 시스템 설계
- 보안 감사 로그 구현

### 🔐 Vault Integration
- HashiCorp Vault 클라이언트 연동
- 시크릿 관리 및 순환
- PKI 인증서 관리
- 암호화 서비스 구현

### 🚀 DevOps Engineer
- Docker/Kubernetes 설정
- CI/CD 파이프라인 구성
- 모니터링/로깅 시스템
- 인프라 자동화

### 📊 Compliance Auditor
- GDPR/HIPAA 컴플라이언스 검토
- 개인정보 처리 방침 작성
- 감사 로그 설계
- 리스크 평가 및 관리

## 💡 효과적인 활용 팁

### 1. 컨텍스트 최적화
- 관련 파일들만 VS Code에서 열기
- 작업 범위를 명확히 명시
- 단계별로 점진적 개발

### 2. 프롬프트 조합
```
@medical @security
환자 데이터를 안전하게 해싱하는 함수를 보안 검토와 함께 작성해줘
```

### 3. 구체적인 요청
- 일반적인 질문보다 구체적인 상황 제시
- AI4RM 프로젝트 특성 언급
- 컴플라이언스 요구사항 명시

### 4. 개발 지침 참조
```
AI_CODING_GUIDELINES.md를 참고하여 FF3 가명화 함수를 작성해줘
```

## ⚠️ 주의사항

### 보안
- 실제 환자 데이터나 개인정보를 프롬프트에 포함하지 마세요
- API 키, 비밀번호 등 민감 정보 노출 금지
- 프로덕션 환경 정보는 예시로만 사용

### 컴플라이언스
- AI 생성 코드도 컴플라이언스 검토 필요
- 법적 요구사항은 전문가와 상의
- 감사 목적으로 AI 사용 이력 기록

### 품질
- AI 제안 코드는 항상 검토 후 사용
- 단위 테스트 작성 및 검증
- 코드 리뷰 프로세스 준수

## 🔄 업데이트 및 유지보수

- 정기적으로 프롬프트 내용 검토 및 업데이트
- 새로운 컴플라이언스 요구사항 반영
- 팀 피드백을 통한 프롬프트 개선
- 버전 관리를 통한 변경 이력 추적

## 📚 추가 자료

- **[AI_CODING_GUIDELINES.md](.github/AI_CODING_GUIDELINES.md)**: 상세한 개발 지침 및 패턴
- **[ai4rm-core.json](.github/copilot/contexts/ai4rm-core.json)**: 프로젝트 컨텍스트 정보
- **Wiki**: 개발 기간 중 시행착오 기록 및 운영 문서
