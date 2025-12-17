# Security Audit & VAPT Report

**Date**: 2025-12-17
**Scope**: Codebase Static Analysis (SAST) & Configuration Review
**Target**: `eduka_backend`

## Executive Summary
The security posture of the application is **GOOD**. No critical code-level vulnerabilities (hardcoded secrets, CSRF bypasses, SQL injection patterns) were found. The primary area for improvement is **Server/Framework Configuration** to enforce stricter browser security policies (HSTS, Headers).

---

## 1. Vulnerability Assessment Findings

### ✅ Passed Checks (Strengths)
*   **No Hardcoded Secrets**: `SECRET_KEY` and API keys are correctly loaded from environment variables.
*   **CSRF Protection**: No instances of `@csrf_exempt` were found; CSRF protection is active globally.
*   **Debug Mode**: Controlled via environment variable (crucial for production).
*   **Host Validation**: `ALLOWED_HOSTS` is properly configured.

### ⚠️ Medium / Low Risk Findings (Configuration)
1.  **Missing HSTS (HTTP Strict Transport Security)**
    *   **Risk**: Low/Medium. Without HSTS, a user could theoretically be downgraded to HTTP by a Man-in-the-Middle before the first redirect.
    *   **Recommendation**: Enable HSTS with a long duration.

2.  **Missing Explicit Security Headers**
    *   **Risk**: Low. Missing headers like `X-Content-Type-Options: nosniff` can expose users to MIME-sniffing attacks. `X-Frame-Options` should be explicitly set to prevent clickjacking.
    *   **Recommendation**: Explicitly set these headers in `settings.py`.

3.  **Cookie Security Dependency**
    *   **Observation**: `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` depend on environment variables.
    *   **Recommendation**: Ensure `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` are set in the production `.env` file.

---

## 2. Remediation Plan

We will apply the following fixes to `settings.py` without causing downtime.

### Fix 1: Enable HSTS
Enforces HTTPS for all future visits.
```python
SECURE_HSTS_SECONDS = 31536000  # 1 Year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Fix 2: Harden Security Headers
Prevents content sniffing and clickjacking.
```python
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Fix 3: CORS Configuration
Ensure `CORS_ALLOWED_ORIGINS` matches the production domain.

---

## 3. Deployment Instructions
1.  **Review**: Confirm the changes in `settings.py`.
2.  **Env**: Verify your production `.env` file has:
    ```bash
    SECURE_SSL_REDIRECT=True
    SESSION_COOKIE_SECURE=True
    CSRF_COOKIE_SECURE=True
    ```
3.  **Deploy**: Pull changes and restart services.

---

## 4. API Security Addendum (Step 2)

### Findings
*   **Permissions**: Most views manually check `IsAuthenticated`, which is good.
*   **Gap**: The project lacks a **Global Default Permission**, meaning if a developer forgets to add `permission_classes`, the view is public by default.
*   **Gap**: No **Throttling (Rate Limiting)** is configured, leaving APIs exposed to brute-force or spam attacks.

### Remediation
We will update `settings.py` to:
1.  **Set Global Default Permission**: `IsAuthenticated` (Safe by default).
2.  **Enable Throttling**: Limit anonymous users to 20/min and authenticated users to 100/min.
