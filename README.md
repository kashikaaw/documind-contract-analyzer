# 📄 DocuMind: AI Contract Analyzer

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-LLM%20Powered-purple.svg)](https://groq.com)

**From phone photo to risk report in 60 seconds.**

An AI-powered contract analysis platform that handles *any* document format—scanned PDFs, phone photos, fax-quality scans—and delivers comprehensive risk assessment with negotiation recommendations.

![DocuMind Demo](https://img.shields.io/badge/Status-Live-brightgreen) 
![Jurisdictions](https://img.shields.io/badge/Jurisdictions-8+-orange)

---

## 🎯 The Problem

Most contract analysis tools fail with real-world documents:

| Document Type | Traditional OCR | DocuMind |
|---------------|-----------------|----------|
| Native PDF | ✅ Works | ✅ Works |
| Scanned PDF | ❌ Poor quality | ✅ AI-enhanced |
| Phone photo (skewed) | ❌ Fails | ✅ Auto-corrects |
| Fax quality | ❌ Unreadable | ✅ Enhanced OCR |
| Mixed format (tables + text) | ❌ Loses structure | ✅ Preserves layout |

**DocuMind solves this** with a multi-layered extraction pipeline powered by Vision AI.

---

## ✨ Features

### 🔍 Intelligent Document Processing
- **Vision-first approach**: Sends images directly to Vision LLM for complex documents
- **Auto-preprocessing**: Deskew, denoise, contrast enhancement
- **Quality detection**: Automatically applies aggressive processing for poor scans
- **Confidence scoring**: Every extraction includes reliability score

### 🌍 Multi-Jurisdiction Support
Smart jurisdiction detection with legally accurate sub-jurisdictions:

| Region | Jurisdictions Covered |
|--------|----------------------|
| **UAE** | DIFC, ADGM, Mainland (Federal) |
| **India** | Central Law + State-specific notes |
| **USA** | Delaware, New York, California, Texas, General |
| **EU** | Germany, France, General EU |
| **UK** | England & Wales |
| **Singapore** | Common Law |

### 📋 Contract Analysis
- **Clause extraction**: Identifies 20+ clause types automatically
- **Risk scoring**: 1-10 score with detailed reasoning for each clause
- **Market benchmarking**: Compares against industry-standard terms
- **Red flag detection**: Highlights concerning provisions

### 💡 Actionable Recommendations
- **Prioritized concerns**: Top issues ranked by severity
- **Negotiation points**: Specific items to address
- **Suggested language**: AI-generated alternative provisions
- **Executive summary**: Ready for leadership briefing

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INPUT                             │
│              (PDF, Image, Scan, Phone Photo)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 1: PREPROCESSING                          │
│  • Deskew Detection    • Noise Reduction    • Contrast Enhance  │
│                    (OpenCV Pipeline)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 2: TEXT EXTRACTION                        │
│     Vision LLM (Gemini)  ──OR──  Tesseract OCR                 │
│              (Primary)           (Fallback)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 3: JURISDICTION DETECTION                 │
│  • Location Keywords    • Legal References    • Currency Signals│
│                  (Smart Auto-Detection)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LAYER 4: CONTRACT ANALYSIS                      │
│  • Clause Extraction    • Risk Scoring    • Market Benchmark    │
│                    (LLM + RAG Pipeline)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                  │
│  • Executive Summary    • Risk Assessment    • Recommendations  │
│  • Clause Breakdown     • Red Flags          • Suggested Terms  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Tesseract OCR (optional, for fallback)
- Poppler (for PDF processing)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/documind-contract-analyzer.git
cd documind-contract-analyzer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install system dependencies**

**Mac:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases

5. **Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

6. **Run the application**
```bash
streamlit run app.py
```

---

## 🔑 API Keys (Free)

| Provider | Get Key | Free Tier |
|----------|---------|-----------|
| **Groq** | [console.groq.com](https://console.groq.com) | 100K tokens/day |
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com/app/apikey) | 60 requests/min |

**Pro tip:** Add both keys for automatic failover when rate limits hit.

---

## 📁 Project Structure

```
documind-contract-analyzer/
├── app.py                    # Streamlit web application
├── document_processor.py     # Multi-format document handling
├── contract_analyzer.py      # AI-powered contract analysis
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
└── README.md                # Documentation
```

---

## 🔧 Technology Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Vision AI** | Google Gemini 2.0 | Best-in-class document understanding |
| **Text LLM** | Groq (Llama 3.3 70B) | Free, fast, high quality |
| **OCR Fallback** | Tesseract + OpenCV | Reliable fallback for simple docs |
| **UI Framework** | Streamlit | Rapid professional interfaces |
| **Image Processing** | OpenCV, Pillow | Industrial-grade preprocessing |

---

## 📋 Supported Clause Types

| Category | Clauses |
|----------|---------|
| **Core Terms** | Parties, Definitions, Scope of Work, Term/Duration |
| **Financial** | Payment Terms, Pricing, Penalties |
| **Risk Allocation** | Liability, Indemnification, Insurance, Warranties |
| **IP & Data** | Intellectual Property, Confidentiality, Data Protection |
| **Exit & Disputes** | Termination, Force Majeure, Dispute Resolution |
| **Restrictions** | Non-Compete, Non-Solicitation, Assignment |

---

## 📊 Risk Scoring

| Score | Level | Meaning |
|-------|-------|---------|
| 9-10 | 🔴 Critical | Immediate attention required |
| 7-8 | 🟠 High | Negotiate before signing |
| 4-6 | 🟡 Medium | Notable but manageable |
| 2-3 | 🟢 Low | Minor concerns |
| 1 | ✅ Standard | Market-standard terms |

---

## 🗺️ Roadmap

- [x] Multi-format document processing
- [x] Vision LLM integration
- [x] Clause extraction and categorization
- [x] Risk scoring with reasoning
- [x] Market benchmark comparison
- [x] Multi-jurisdiction support
- [x] Smart jurisdiction auto-detection
- [x] API failover system
- [ ] Batch processing (multiple contracts)
- [ ] Contract comparison (redline view)
- [ ] Custom benchmark upload
- [ ] API endpoint for integration
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

This tool is for informational purposes only and does not constitute legal advice. Always consult qualified legal counsel for contract review and negotiation.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Kashika Wanchoo**
- Email: kashikaaw@gmail.com
- LinkedIn: [Connect with me](https://linkedin.com/in/YOUR_LINKEDIN)

---

## ⭐ Support

If this project helped you, please give it a ⭐ on GitHub!

---

*Built with ❤️ using Python, Streamlit, and cutting-edge AI*
