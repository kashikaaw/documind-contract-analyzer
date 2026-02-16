# Contributing to DocuMind

First off, thank you for considering contributing to DocuMind! 🎉

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs what actually happened
- **Screenshots** if applicable
- **Environment details** (OS, Python version, browser)

### 💡 Suggesting Features

Feature suggestions are welcome! Please include:

- **Use case**: Why would this feature be useful?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought about

### 🔧 Pull Requests

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes thoroughly
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### 📝 Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Comment complex logic

### 🧪 Testing

- Test with various document formats (PDF, images, scans)
- Test with different jurisdictions
- Verify rate limit handling works
- Check UI renders correctly

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/documind-contract-analyzer.git
cd documind-contract-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your API keys to .env

# Run the app
streamlit run app.py
```

## Areas We Need Help

- 🌍 **More jurisdictions**: Add legal frameworks for more countries
- 🔤 **Multi-language**: Support contracts in other languages
- 📊 **Better benchmarks**: More industry-specific clause benchmarks
- 🧪 **Testing**: Unit tests and integration tests
- 📚 **Documentation**: Improve docs and add examples

## Questions?

Feel free to open an issue or reach out to the maintainers.

Thank you for helping make DocuMind better! 🙏
