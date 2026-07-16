# Security Policy

## Supported Versions
Only the latest version on the `main` branch is supported with security updates. 

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an email to the project maintainers. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

Please provide the following details:
- A description of the vulnerability.
- Steps to reproduce the vulnerability.
- Potential impact of the vulnerability.
- Any suggested mitigations.

## Scope

This project involves integrations with local and remote AI APIs (Ollama, Stable Diffusion WebUI, DeepSeek, etc.).

Security considerations:
- **API Keys**: Ensure `DEEPSEEK_API_KEY` and other credentials are NOT committed to version control. Use `.env.local` or environment variables in production.
- **Service Endpoints**: `LLM_API_URL` and other service URLs are validated to prevent accidental arbitrary requests.
- **Port Checking**: The `service_check.py` handles thread-safe checks to local ports (e.g. 11434, 7860) without raising exceptions or leaking host states.
- **File Parsing**: We rely on standard libraries (`yaml.safe_load`, `json.load`) to parse data from `config/` and `data/` directories, preventing code injection via malformed configs.
