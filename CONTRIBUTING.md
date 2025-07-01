# Contributing to QR File Transfer Tool

Thank you for your interest in contributing to the QR File Transfer Tool! This document provides guidelines and information for contributors.

## 🎯 Project Goals

This project aims to provide a professional-grade, secure CLI tool for file transfer using QR codes, specifically designed for:
- Air-gapped systems and secure environments
- Cross-platform compatibility (Windows, macOS, Linux)
- Enterprise-grade security with AES-256 encryption
- Professional user experience similar to tools like pandoc or git

## 🚀 Getting Started

### Development Environment Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/qr-file-transfer.git
   cd qr-file-transfer
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .  # Install in development mode
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   qr --version
   qr generate --help
   ```

### Project Structure

```
qr-file-transfer/
├── qr.py                    # Main unified CLI entry point
├── qr_enhanced.py           # QR generation engine with encryption
├── qr_scan.py              # Batch QR image scanning
├── qr_rebuild.py           # Basic file reconstruction
├── qr_rebuild_encrypted.py # Encrypted file reconstruction
├── qr_rebuild_verified.py  # Verified reconstruction with checksums
├── qr_rebuild_spaces.py    # Tab-to-space conversion reconstruction
├── qr_config.py            # Configuration management
├── requirements.txt        # Python dependencies
├── README.md              # Main documentation
├── TODO.md                # Development roadmap
├── LICENSE                # MIT License
└── CONTRIBUTING.md        # This file
```

## 🛠️ Development Guidelines

### Code Style

- **Python Style**: Follow PEP 8 guidelines
- **Documentation**: Use clear docstrings for functions and classes
- **Comments**: Explain complex logic, especially security-related code
- **Error Handling**: Provide informative error messages
- **Cross-Platform**: Ensure code works on Windows, macOS, and Linux

### Security Considerations

This tool handles sensitive data and encryption. When contributing:

- **Security Review**: All cryptographic changes require extra scrutiny
- **No Hardcoded Secrets**: Never commit passwords, keys, or sensitive data
- **Input Validation**: Validate all user inputs thoroughly
- **Memory Safety**: Clear sensitive data from memory when possible
- **Dependencies**: Keep cryptographic dependencies up to date

### CLI Interface Standards

Maintain consistency with the pandoc-style interface:

- **Subcommands**: Use clear, descriptive subcommand names
- **Help Text**: Provide comprehensive help with examples
- **Error Messages**: Give actionable error messages
- **Progress Feedback**: Show progress for long operations
- **Return Codes**: Use appropriate exit codes (0 = success, 1 = error)

## 📝 Making Changes

### Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write clean, documented code
   - Test thoroughly on multiple platforms
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   # Test basic functionality
   qr generate temp.txt --sheet --verbose
   qr config show
   
   # Test encryption
   qr generate secret.txt --encrypt --verbose
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Commit Message Format

Use clear, descriptive commit messages:

```
Type: Brief description

Optional longer explanation of what this commit does and why.

- Add bullet points for specific changes
- Reference issues with #123
```

**Types**: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Docs`, `Test`

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Environment**: OS, Python version, tool version
- **Command**: Exact command that failed
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happened
- **Error Messages**: Full error output
- **Reproduction Steps**: Minimal steps to reproduce

### Feature Requests

For new features, please describe:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Any alternative approaches considered?
- **Impact**: How does this affect existing functionality?

## 🧪 Testing

### Manual Testing

Test your changes with:

```bash
# Basic generation
qr generate README.md --sheet --verbose

# Encryption workflow
qr generate secret.txt --encrypt --sheet
qr rebuild ./scanned_chunks/ --encrypted

# Cross-platform paths
qr scan ./test_images/ --auto-rebuild

# Configuration
qr config show
qr config reset
```

### Platform Testing

If possible, test on multiple platforms:
- **Windows**: PowerShell and Command Prompt
- **macOS**: Terminal
- **Linux**: Various distributions

## 📚 Documentation

### README Updates

When adding features, update:
- Command examples in README.md
- Help text and usage examples
- Installation instructions if needed

### Code Documentation

- **Docstrings**: Document all public functions
- **Inline Comments**: Explain complex algorithms
- **Type Hints**: Use Python type hints where helpful

## 🏷️ Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to CLI interface
- **MINOR**: New features, maintaining compatibility
- **PATCH**: Bug fixes and minor improvements

## 💬 Community

### Communication

- **GitHub Issues**: For bugs, features, and questions
- **Pull Requests**: For code contributions
- **Discussions**: For general questions and ideas

### Code of Conduct

Be respectful and constructive in all interactions. This is a professional tool used in security-sensitive environments, so maintain high standards for:

- Code quality and security
- Documentation and examples
- Respectful communication
- Constructive feedback

## 🎉 Recognition

Contributors will be recognized in:
- Release notes for significant contributions
- README.md contributor section (when established)
- GitHub contributor statistics

Thank you for helping make QR File Transfer Tool better! 🚀 