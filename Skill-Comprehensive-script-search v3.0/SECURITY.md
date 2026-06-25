# Security Policy

## Supported Versions

The following table shows which versions of find-script are currently receiving
security updates:

| Version | Supported          |
|---------|--------------------|
| 3.0.x   | :white_check_mark: |
| 2.x.x   | :x:                |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

Only the latest major version receives security fixes. Please upgrade before
filing a vulnerability report.

## Reporting a Vulnerability

**Please do NOT file a public GitHub issue for security vulnerabilities.**

Send reports privately to
[security@find-script.local](mailto:security@find-script.local).

You should receive an acknowledgment within 72 hours. If you do not, please
follow up to ensure we received your report.

### What to include

A good vulnerability report should contain:

- A clear, descriptive title
- A summary of the issue and its impact
- Step-by-step reproduction instructions
- Affected version(s) and commit SHA(s)
- Your assessment of severity (Low / Medium / High / Critical)
- Any known mitigations or workarounds
- (Optional) Suggested fix or patch

### What to expect

1. **Acknowledgment** within 72 hours
2. **Initial assessment** within 7 days
3. **Status updates** at least every 14 days until resolved
4. **Credit** to the reporter in the release notes (unless you prefer to remain
   anonymous)
5. **Coordinated disclosure** — we will agree on a disclosure timeline that
   gives users time to upgrade

## Scope

The following are in scope for security reports:

- **SSRF / URL validation** — find-script fetches URLs returned by search
  engines. Bypasses of the SSRF guard (RFC1918 / loopback / link-local blocking)
  are in scope.
- **Path traversal** — any user-controllable path component that escapes the
  download sandbox
- **Command injection** — anywhere user input flows into a shell, including
  URLs and search keywords
- **TOCTOU / race conditions** — concurrent download/analyze issues
- **Copyright bypass** — any way to skip the `--allow-copyrighted` requirement
  on copyrighted content
- **Dependency vulnerabilities** — third-party binaries or libraries bundled in
  `vendor/`
- **Information disclosure** — leaks of user queries, downloaded content paths,
  or analysis results

## Out of Scope

- Issues requiring physical access to the user's machine
- Issues in third-party search engines or websites we link to
- Social-engineering attacks against the user
- Denial-of-service against the search engines (we already rate-limit)
- "The script is too slow" / performance issues
- Bugs in macOS/Linux/Windows themselves

## Safe Harbor

We will not pursue legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data destruction, or
  service interruption
- Only interact with accounts they own or have explicit permission to access
- Stop testing immediately if they encounter user data and report it
- Do not exploit a vulnerability beyond what is necessary to demonstrate it
- Comply with the disclosure timeline we agree on

## Security Best Practices for Users

When using find-script, please:

- Always review the `copyright_tag` field in JSON output before opening
  downloaded scripts
- Do not point the `--save-path` at sensitive directories; downloaded scripts
  may contain copyrighted material
- Keep `find-script` updated to the latest version
- Use `--no-auto-download` if you only want search results
- Read [references/anti-patterns.md](references/anti-patterns.md) to avoid
  common pitfalls

## Acknowledgments

We thank the following security researchers for responsibly disclosing issues:

- (No reports yet — your name could be here)
