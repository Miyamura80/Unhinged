# Unhinged

**AI-Powered Dating Profile Analysis & Automation System**

Automated profile extraction, photo analysis, and comprehensive feature inference using advanced AI agents.

## Overview

**Unhinged** is an AI-powered system that automates profile analysis from the Hinge dating app. It combines mobile automation (ADB), computer vision, and large language models to extract detailed insights from dating profiles that go beyond what's explicitly stated.

The system captures profile information from Android devices, analyzes photos using AI, and generates comprehensive reports including inferred personality traits, lifestyle preferences, and dating style classification.

## Key Features

### 🤖 Intelligent Mobile Automation
- **ADB-based device control** - Automated swiping, tapping, and screenshot capture
- **XML UI hierarchy parsing** - Precise element location and interaction
- **Smart photo detection** - Automatically identifies and captures all profile photos
- **Complete profile extraction** - Age, location, height, job, education, prompts, and more

### 🎨 Advanced Photo Analysis
- **Multi-photo feature extraction** - Analyzes physical attributes, style, and context
- **Activity & location inference** - Detects settings, activities, and social contexts
- **Physical attribute detection** - Hair color, piercings, makeup level, freckles, and more
- **Aggregated analysis** - Synthesizes insights across multiple photos

### 🧠 AI-Powered Profile Synthesis
- **DSPy ReAct agents** - Intelligent reasoning and analysis workflow
- **Multi-LLM support** - Google Gemini, OpenAI, Claude, Groq, Perplexity
- **Comprehensive profiling** - Dating style, lifestyle, personality traits, interests
- **Lifestyle inference** - Party frequency, activity level, dating intentions

### 📊 Observability & Monitoring
- **Langfuse integration** - Track AI agent behavior, costs, and performance
- **Structured logging** - Session-based tracking with Loguru
- **Cost monitoring** - Per-analysis token usage and cost tracking
- **Agent decision tracing** - Full visibility into AI reasoning steps

### 🛠️ Developer Experience
- **Cursor IDE integration** - Native `.cursorrules` for consistent coding
- **Configuration-driven** - YAML-based settings with environment variable support
- **Type-safe models** - Dataclass-based profile and analysis structures
- **Comprehensive testing** - Pytest suite with health checks

## How It Works

```mermaid
graph TD
    A[Android Device via ADB] --> B[UI Hierarchy Dump]
    B --> C[HingeAPI Parser]
    C --> D[Profile Data Extraction]
    C --> E[Photo Capture]

    E --> F[Individual Photo Analysis]
    F --> G[DSPy ReAct Agent + Gemini]
    G --> H[Physical Attributes]
    G --> I[Activities & Context]

    D --> J[Profile Synthesis Agent]
    H --> J
    I --> J

    J --> K[Comprehensive Profile Report]
    K --> L[Dating Style Classification]
    K --> M[Lifestyle Inference]
    K --> N[Interest & Personality Traits]

    G -.-> O[Langfuse Tracing]
    J -.-> O
```

### Workflow Phases

1. **Capture Phase** - ADB extracts UI hierarchy, parses profile data, and captures photos
2. **Analysis Phase** - AI agents analyze each photo for features, activities, and attributes
3. **Synthesis Phase** - Aggregated analysis produces comprehensive profile report
4. **Monitoring Phase** - Langfuse tracks all LLM calls, costs, and agent decisions

## Requirements

### Software Dependencies
- **Python 3.12+**
- **[Rye](https://rye.astral.sh/)** - Python package manager
  ```bash
  curl -sSf https://rye.astral.sh/get | bash
  ```
- **ADB (Android Debug Bridge)**
  ```bash
  # macOS
  brew install android-platform-tools

  # Linux (Debian/Ubuntu)
  sudo apt-get install android-tools-adb

  # Windows
  # Download from: https://developer.android.com/tools/releases/platform-tools
  ```

### Hardware Requirements
- **Android device** with USB debugging enabled
- **USB cable** for device connection

### API Keys (at least one required)
- Google Gemini API key (recommended - default model)
- OpenAI API key (optional)
- Anthropic Claude API key (optional)
- Groq API key (optional)
- Perplexity API key (optional)

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/Miyamura80/Unhinged.git
cd Unhinged
rye sync
```

### 2. Configure Environment Variables
```bash
# Create .env file
cp .env.example .env  # If example exists, or create new

# Edit .env and add your API keys
echo "GEMINI_API_KEY=your_api_key_here" >> .env
echo "DEV_ENV=development" >> .env
```

### 3. Enable USB Debugging on Android
1. Go to **Settings → About Phone**
2. Tap **Build Number** 7 times to enable Developer Mode
3. Go to **Settings → Developer Options**
4. Enable **USB Debugging**
5. Connect device via USB and authorize the computer

### 4. Verify ADB Connection
```bash
adb devices
# Should show your device listed
```

### 5. Run Demo
```bash
make demo
```

## Usage

```bash
make all        # Run main application
make demo       # Run demo workflow
make test       # Run test suite
make lint       # Format code with Black
make vulture    # Detect dead code
make show-mobile-screen  # Stream device screen to desktop
```

## Ethical Considerations

⚠️ **IMPORTANT ETHICAL NOTICE** ⚠️

This tool is designed for **research and educational purposes** only. Users must:

- ✅ Only analyze their own profiles or profiles with explicit consent
- ✅ Comply with Hinge's Terms of Service
- ✅ Respect privacy and data protection laws (GDPR, CCPA, etc.)
- ✅ Use insights responsibly and ethically

- ❌ Do not use for harassment, stalking, or discrimination
- ❌ Do not scrape or store data without consent
- ❌ Do not violate platform terms of service
- ❌ Do not use for commercial purposes without proper authorization

**The developers assume no liability for misuse of this software.**

## Credits

This project uses the following open-source tools:

- [DSPy](https://github.com/stanfordnlp/dspy) - Stanford NLP AI framework
- [LiteLLM](https://github.com/BerriAI/litellm) - LLM provider abstraction
- [Langfuse](https://langfuse.com/) - AI observability platform
- [Rye](https://rye.astral.sh/) - Python package manager
- [Cursor](https://cursor.com) - AI-powered code editor

## License

MIT License - see [LICENSE](LICENSE) file for details

## About the Core Contributors

Created by researchers interested in AI-powered profile analysis and mobile automation. Contributions welcome!

---

<p align="center">
  <i>Built with DSPy, Gemini AI, and ADB automation</i>
</p>
