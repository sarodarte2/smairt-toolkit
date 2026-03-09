# Contributing to SMAIRT Cookiecutter

Thank you for your interest in contributing to SMAIRT! This document provides guidelines for contributing to the project.

## Ways to Contribute

### Reporting Issues

- **Bug Reports**: If you find a bug, please create an issue using the Bug Report template
- **Feature Requests**: Have an idea for improvement? Use the Feature Request template
- **Questions**: Not sure about something? Use the Question template

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test your changes**: Generate a project using the template and verify it works
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**: Describe your changes and link any related issues

### Documentation Improvements

Documentation improvements are always welcome! This includes:
- Fixing typos or unclear explanations
- Adding examples
- Improving the README
- Enhancing the generated project documentation

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/smairt-cookiecutter.git
cd smairt-cookiecutter

# Install cookiecutter for testing
pip install cookiecutter

# Test the template locally
cookiecutter . --no-input
```

## Testing Changes

Before submitting a PR, please test your changes:

1. Generate a new project from the template
2. Verify the project structure is correct
3. Check that all placeholder variables are properly substituted
4. Test any hooks (pre/post generation scripts)

## Code Style

- Use clear, descriptive names
- Add comments for complex logic
- Follow existing patterns in the codebase
- Keep the template structure intuitive

## Questions?

If you have questions about contributing, feel free to open an issue with the Question template.

Thank you for helping improve SMAIRT!
