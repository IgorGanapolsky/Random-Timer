# SuperPassword 🧠 AI-Powered Password Manager

[![CI Status](https://github.com/IgorGanapolsky/SuperPassword/workflows/CI/badge.svg?branch=main)](https://github.com/IgorGanapolsky/SuperPassword/actions)
[![CodeQL](https://github.com/IgorGanapolsky/SuperPassword/workflows/CodeQL/badge.svg)](https://github.com/IgorGanapolsky/SuperPassword/security/code-scanning)
[![codecov](https://codecov.io/gh/IgorGanapolsky/SuperPassword/branch/main/graph/badge.svg)](https://codecov.io/gh/IgorGanapolsky/SuperPassword)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**The world's first password manager with true AI intelligence** - built with React Native + Expo frontend and Eko-powered Node.js AI backend.

## 🚀 Revolutionary AI Features

- **🔍 AI Vault Security Audits** - Claude-powered vulnerability analysis
- **🎣 Real-time Phishing Detection** - Intelligent URL threat analysis  
- **🔄 Smart Password Rotation Planning** - AI-optimized rotation schedules
- **📊 Executive Security Reports** - Professional insights and trends
- **🤖 Multi-Agent Development** - Claude + Git worktrees workflow
- **🛡️ Proactive Breach Monitoring** - HaveIBeenPwned integration with AI analysis

## ✨ Core Features

### 🆓 Free Tier
- Clean Material Design interface with gradient background
- Password generation with customizable length (8-50 characters)
- Toggle options for uppercase, lowercase, numbers, special characters
- Real-time password strength meter with color coding
- One-tap copy to clipboard with success animation
- Password history (last 10 generated passwords) with timestamps
- Dark mode toggle with system preference detection
- Haptic feedback for interactions
- **Basic AI vault audits (10 passwords max)**

### 💎 Premium Tiers

#### Plus Tier ($5.99/mo)
- Unlimited password history
- **Advanced AI security audits**
- **Real-time breach monitoring**
- Cloud sync across devices
- Export passwords to CSV
- No advertisements

#### Pro Tier ($9.99/mo)
- Everything in Plus
- **AI-powered password rotation planning**
- **Executive security reports**
- **Phishing URL protection**
- Advanced security settings
- Custom character sets and exclusion rules
- Bulk password generation (up to 100 at once)

#### Family Tier ($14.99/mo)
- Everything in Pro
- **Multi-user AI features**
- **Family security dashboard**
- 6 user accounts
- Shared password vaults

#### Enterprise (Custom Pricing)
- Everything in Family
- **Advanced AI analytics**
- **Custom security policies**
- SSO integration
- Admin dashboard
- Priority support

## 🏗️ Architecture

### Mobile App (React Native + Expo)
```
/src
├── components/     # Reusable UI components
├── contexts/       # React Context providers  
├── hooks/         # Custom React hooks
├── navigation/    # Navigation configuration
├── screens/       # Feature-specific screens
├── services/      # Business logic layer
├── types/         # TypeScript definitions
└── utils/         # Helper utilities
```

### AI Backend Service (Node.js + Eko)
```
/server/sp-ai-service/
├── src/
│   ├── agents/     # Specialized AI agents
│   ├── routes/     # API endpoints
│   ├── services/   # Core business logic
│   └── types/      # TypeScript definitions
├── package.json    # Node.js dependencies
└── test-demo.mjs   # AI features demo
```

## 🛠️ Technology Stack

### Frontend
- **React Native 0.79.5** with Expo SDK 53
- **TypeScript 5.x** with comprehensive type safety
- **React Navigation 7.x** with bottom tabs
- **React Native Paper** for Material Design
- **AsyncStorage** for local persistence
- **Sentry** for error monitoring

### AI Backend
- **🤖 Eko Framework 3.0.2** for agentic workflows
- **👤 Claude 3.5 Sonnet** for AI analysis
- **🔍 Node.js + Fastify** backend service
- **🔒 Firebase Authentication & Firestore**
- **🌐 HaveIBeenPwned API** integration
- **📊 Real-time security analytics**

### Testing & Quality
- **Jest + React Testing Library** for unit tests
- **E2E testing** with Detox (planned)
- **SonarCloud** for code quality
- **CodeQL** for security analysis
- **Codecov** for test coverage

### CI/CD & Security
- **GitHub Actions** for automated pipelines
- **EAS Build** for mobile app distribution
- **OWASP Dependency-Check** for vulnerabilities
- **Snyk** for security monitoring
- **Branch protection** with required reviews

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator (Mac only) or Android Emulator

### 1. Clone and Setup
```bash
git clone https://github.com/IgorGanapolsky/SuperPassword.git
cd SuperPassword
git checkout develop
npm install
```

### 2. Mobile App Development
```bash
# Start the mobile development server
npm start

# Run on iOS Simulator
npm run ios

# Run on Android Emulator  
npm run android
```

### 3. AI Backend Development
```bash
# Navigate to AI service
cd server/sp-ai-service

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start AI service in development mode
npm run dev

# Run AI feature demos
./test-demo.mjs
```

### 4. Test Everything
```bash
# Mobile app tests
npm test

# Backend tests
cd server/sp-ai-service && npm test

# Lint everything
npm run lint
```

## 🤖 Multi-Agent Development Workflow

We use **git worktrees** + **specialized Claude agents** for parallel development:

### Git Worktrees Setup
```bash
# Create parallel development environments
git worktree add ../sp-ai-intelligence -b feature/ai-intelligence
git worktree add ../sp-secure-storage -b feature/secure-storage  
git worktree add ../sp-biometrics -b feature/biometrics
git worktree add ../sp-ci-hardening -b chore/ci-hardening

# List all worktrees
git worktree list
```

### Agent Specialization
- **Security Claude**: E2EE implementation, SecureStore, key rotation
- **Auth Claude**: Biometrics, session hardening, Firebase Auth
- **AI Claude**: Eko integration, intelligence features, backend API
- **DevOps Claude**: CI/CD, testing, automation, deployment

### Development Process
1. **Plan & Document** in `docs/agents/{feature}/PLAN.md`
2. **TDD Loop**: Write failing tests → Make pass → Refactor  
3. **Multi-Agent Review**: Agent A implements → Agent B reviews → Agent C verifies
4. **Conventional Commits**: `feat: implement AI vault auditing`
5. **Open PR** with clear scope and rollback plan

## 🔒 AI Intelligence Features

### 🔍 Vault Security Audit
```bash
POST /api/v1/intelligence/audit
```
- AI-powered password vulnerability analysis
- Security score calculation (0-100)
- Identifies weak, breached, duplicate, and stale passwords  
- Actionable recommendations with priority rankings
- Executive summary for non-technical users

### 🎣 Phishing URL Detection  
```bash
POST /api/v1/intelligence/phishing-check
```
- Real-time URL threat analysis
- Domain lookalike detection
- Phishing pattern recognition
- Risk level assessment (LOW/MEDIUM/HIGH/CRITICAL)
- Safe alternative suggestions

### 🔄 Password Rotation Planning
```bash
POST /api/v1/intelligence/rotation-plan  
```
- AI-optimized rotation schedules
- Priority-based timeline creation
- Site-specific rotation guidance
- Time estimation and milestone tracking
- User preference integration

### 📊 Security Reports & Analytics
```bash
POST /api/v1/intelligence/generate-report
```
- Executive, technical, and user-friendly formats
- Security trends and improvement tracking
- Personalized recommendations
- Visual charts and insights
- Exportable reports

## 🏃‍♂️ Quick Commands for AI Agents

### Architecture Check
```bash
# Verify current architecture
cat WARP.md | grep -A 10 "AI INTELLIGENCE"

# Check service health  
cd server/sp-ai-service && ./test-demo.mjs --health

# Run comprehensive AI demos
cd server/sp-ai-service && ./test-demo.mjs
```

### Development Workflow
```bash
# Switch to specific worktree
cd ../sp-ai-intelligence

# Test specific AI features
./test-demo.mjs --audit          # Vault security audit
./test-demo.mjs --phishing       # Phishing detection  
./test-demo.mjs --rotation       # Rotation planning

# Check service logs
tail -f server/sp-ai-service/server.log
```

## 🚢 Deployment

### Mobile App (EAS Build)
```bash
# Configure EAS (first time)
eas configure

# Build for development
eas build --profile development --platform all

# Build for production
eas build --profile production --platform all

# Submit to app stores
eas submit --platform all
```

### AI Backend Service
- **Platform**: Railway, Render, or DigitalOcean
- **Environment**: Node.js 20+, PM2 process manager
- **Database**: Firebase Firestore for user data & audit history
- **Monitoring**: Sentry error tracking, Fastify logging
- **Security**: Firebase Auth tokens, rate limiting, API key protection

## 📈 Business Model

### Revenue Streams
1. **Subscription Tiers**: $5.99-$14.99/month for AI-powered features
2. **Enterprise Licensing**: Custom pricing for businesses
3. **API Access**: White-label AI security for other password managers
4. **Professional Services**: Security consulting and implementation

### Competitive Advantages
- **First-to-market** with true AI intelligence in password management
- **Advanced threat detection** with real-time phishing and breach monitoring
- **Executive-grade reporting** for business and enterprise users
- **Multi-agent development** enabling rapid innovation and feature delivery

## 🤝 Contributing

1. **Fork the repository** and create your feature branch from `develop`
2. **Follow the multi-agent workflow** outlined above
3. **Write comprehensive tests** for all new features
4. **Update documentation** including WARP.md for architecture changes
5. **Ensure CI passes** before submitting pull requests
6. **Use conventional commits** for clear change tracking

### Development Guidelines
- **Security First**: All password data must be encrypted and never logged
- **AI Ethics**: Transparent AI decision-making with user control
- **Performance**: Mobile-first with <3s AI response times
- **Accessibility**: WCAG 2.1 AA compliance for all UI elements
- **Privacy**: GDPR/CCPA compliant with minimal data collection

## 🆘 Support & Community

- **📚 Documentation**: Full API docs at `http://localhost:3001/docs`
- **🐛 Bug Reports**: GitHub Issues with detailed reproduction steps
- **💡 Feature Requests**: GitHub Discussions with use case examples
- **🔒 Security Issues**: Private disclosure via security@superpassword.app
- **💬 Community**: Discord server for developers and users

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**SuperPassword** - The future of password security is here. 🚀🔐🧠
