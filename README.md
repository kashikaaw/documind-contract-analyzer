# DocuMind: AI Contract Analyzer

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A contract analysis tool that processes any document format—scanned PDFs, phone photos, fax-quality scans—and delivers risk assessment with negotiation recommendations.

---

## Problem

Most contract analysis tools fail with real-world documents:

| Document Type | Traditional OCR | DocuMind |
|---------------|-----------------|----------|
| Native PDF | Works | Works |
| Scanned PDF | Poor quality | AI-enhanced |
| Phone photo (skewed) | Fails | Auto-corrects |
| Fax quality | Unreadable | Enhanced OCR |
| Mixed format (tables + text) | Loses structure | Preserves layout |

DocuMind solves this with a multi-layered extraction pipeline powered by Vision AI.

---

## Features

### Document Processing
- Vision-first approach using LLMs for complex documents
- Auto-preprocessing: deskew, denoise, contrast enhancement
- Quality detection with automatic aggressive processing for poor scans
- Confidence scoring for every extraction

### Multi-Jurisdiction Support

| Region | Jurisdictions Covered |
|--------|----------------------|
| UAE | DIFC, ADGM, Mainland (Federal) |
| India | Central Law + State-specific notes |
| USA | Delaware, New York, California, Texas, General |
| EU | Germany, France, General EU |
| UK | England and Wales |
| Singapore | Common Law |

### Contract Analysis
- Clause extraction: 20+ clause types identified automatically
- Risk scoring: 1-10 scale with detailed reasoning
- Market benchmarking against industry-standard terms
- Red flag detection for concerning provisions

### Recommendations
- Prioritized concerns ranked by severity
- Specific negotiation points
- AI-generated alternative language suggestions
- Executive summary for leadership briefing

---

## Architecture

```
+------------------------------------------------------------------+
|                      DOCUMENT INPUT                              |
|              (PDF, Image, Scan, Phone Photo)                     |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                      PREPROCESSING                               |
|       Deskew Detection / Noise Reduction / Contrast Enhance      |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                      TEXT EXTRACTION                             |
|            Vision LLM (Primary) -- Tesseract OCR (Fallback)      |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   JURISDICTION DETECTION                         |
|       Location Keywords / Legal References / Currency Signals    |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    CONTRACT ANALYSIS                             |
|         Clause Extraction / Risk Scoring / Market Benchmark      |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                          OUTPUT                                  |
|    Executive Summary / Risk Assessment / Recommendations         |
+------------------------------------------------------------------+
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Tesseract OCR (optional, for fallback)
- Poppler (for PDF processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/kashikaaw/documind-contract-analyzer.git
cd documind-contract-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### System Dependencies

Mac:
```bash
brew install tesseract poppler
```

Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

Windows:
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases

### Configuration

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Run

```bash
streamlit run app.py
```

---

## API Keys

| Provider | URL | Free Tier |
|----------|-----|-----------|
| Groq | console.groq.com | 100K tokens/day |
| Google Gemini | aistudio.google.com | 60 requests/min |

Add both keys for automatic failover when rate limits are reached.

---

## Project Structure

```
documind-contract-analyzer/
├── app.py                    # Streamlit web application
├── document_processor.py     # Multi-format document handling
├── contract_analyzer.py      # Contract analysis engine
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
└── README.md                 # Documentation
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Vision AI | Google Gemini 2.0 |
| Text LLM | Groq (Llama 3.3 70B) |
| OCR Fallback | Tesseract + OpenCV |
| UI Framework | Streamlit |
| Image Processing | OpenCV, Pillow |

---

## Supported Clause Types

| Category | Clauses |
|----------|---------|
| Core Terms | Parties, Definitions, Scope of Work, Term/Duration |
| Financial | Payment Terms, Pricing, Penalties |
| Risk Allocation | Liability, Indemnification, Insurance, Warranties |
| IP and Data | Intellectual Property, Confidentiality, Data Protection |
| Exit and Disputes | Termination, Force Majeure, Dispute Resolution |
| Restrictions | Non-Compete, Non-Solicitation, Assignment |

---

## Risk Scoring

| Score | Level | Meaning |
|-------|-------|---------|
| 9-10 | Critical | Immediate attention required |
| 7-8 | High | Negotiate before signing |
| 4-6 | Medium | Notable but manageable |
| 2-3 | Low | Minor concerns |
| 1 | Standard | Market-standard terms |

---

## Roadmap

- [x] Multi-format document processing
- [x] Vision LLM integration
- [x] Clause extraction and categorization
- [x] Risk scoring with reasoning
- [x] Market benchmark comparison
- [x] Multi-jurisdiction support
- [x] Smart jurisdiction auto-detection
- [x] API failover system
- [ ] Batch processing
- [ ] Contract comparison (redline view)
- [ ] Custom benchmark upload
- [ ] API endpoint
- [ ] Multi-language support

---

## Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/new-feature)
3. Commit changes (git commit -m 'Add new feature')
4. Push to branch (git push origin feature/new-feature)
5. Open a Pull Request

---

## Disclaimer

This tool is for informational purposes only and does not constitute legal advice. Consult qualified legal counsel for contract review and negotiation.

---

## License

MIT License - see LICENSE for details.

---

## Author

Kashika Wanchoo
kashikaaw@gmail.com
