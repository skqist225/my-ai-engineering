# OWASP Top 10 for CI/CD and DevSecOps Guidelines

## 1. CI/CD Security Risks

### Risk 1: Insufficient Flow Control Mechanisms (CICD-SEC-1)
- **Severity:** HIGH
- **Description:** Code and configuration changes can be deployed directly to production without code reviews, status checks, or two-person approval rules.
- **Offending Pattern:** GitHub Actions pushing directly from unreviewed branches; unprotected `main` branches.
- **Remediation:** Enforce branch protection rules requiring at least 1 pull request approval, passing CI status checks, and linear git history.

### Risk 2: Inadequate Identity and Access Management (CICD-SEC-2)
- **Severity:** CRITICAL
- **Description:** Long-lived static cloud credentials stored in CI/CD pipeline secrets (e.g. AWS Access Keys, Service Account JSONs).
- **Remediation:** Adopt OpenID Connect (OIDC) workload identity federation to obtain short-lived, scoped access tokens dynamically without storing long-lived static secrets.

### Risk 3: Dependency Chain Abuse / Supply Chain Vulnerabilities (CICD-SEC-3)
- **Severity:** HIGH
- **Description:** Untracked dependencies, unpinned third-party actions, or missing checksum validation.
- **Offending Pattern:** `uses: actions/checkout@v4` without commit SHA pinning, or unverified pip/npm packages.
- **Remediation:** Pin external GitHub Actions to full commit SHAs (`uses: actions/checkout@b4ffde... # v4.1.1`), generate Software Bill of Materials (SBOMs), and use Cosign to verify image provenance.

### Risk 4: Poisoned Pipeline Execution (PPE) (CICD-SEC-4)
- **Severity:** CRITICAL
- **Description:** Running unvetted pull request code inside CI runners that have access to production secrets or internal networks.
- **Offending Pattern:** `pull_request_target` workflows checking out PR head code and referencing repository secrets.
- **Remediation:** Never checkout untrusted pull request code in `pull_request_target` workflows. Use standard `pull_request` triggers where secrets are not accessible to forks.

### Risk 5: Insufficient Secret Scrubbing and Credential Leaks (CICD-SEC-5)
- **Severity:** HIGH
- **Description:** Hardcoded tokens in commits, logs printing environment variables containing secrets, or unmasked output.
- **Remediation:** Run automated pre-commit secret scanners (Gitleaks, TruffleHog) and ensure CI logs mask sensitive variables.
