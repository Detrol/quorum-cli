# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in Quorum, please report it responsibly.

### How to Report

1. **Do NOT** open a public issue for security vulnerabilities
2. Email the maintainers directly or use GitHub's private vulnerability reporting feature
3. Include as much information as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Updates**: We will keep you informed of our progress
- **Fix**: We will work on a fix and coordinate disclosure with you
- **Credit**: With your permission, we will credit you in the release notes

### Scope

Security issues we're interested in:

- Authentication/authorization bypasses
- Code injection vulnerabilities
- Sensitive data exposure
- Dependency vulnerabilities with actual impact

### Out of Scope

- API key exposure (users are responsible for their own keys)
- Issues requiring physical access
- Social engineering attacks
- Denial of service attacks that require significant resources

## Security Best Practices for Users

1. **Protect your API keys**: Never commit `.env` files or share API keys
2. **Use environment variables**: Store sensitive data in environment variables
3. **Keep dependencies updated**: Run `pip install -U` regularly
4. **Review file context**: Be cautious when using `/file` command with sensitive files

## Dependencies

We regularly monitor and update dependencies for security patches. If you notice an outdated dependency with known vulnerabilities, please open an issue.
