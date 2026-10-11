# 05 - Structured Outputs and Schema Enforcement with Instructor

In a software architecture, software modules do not talk to each other using conversational English paragraphs. A REST endpoint, a message queue, a database, or a Kubernetes controller requires **strictly typed, validated data schemas**.

If an LLM returns:
```text
"Here is the issue: In Dockerfile line 12, user is root. Severity is High.
Remediation: Add USER nonroot."
```
Downstream code must write brittle regex parsers to figure out what file was affected, what line number it was, and what the severity level was. If the model says `"pretty high"` instead of `"HIGH"`, a security pipeline breaks.

**Instructor** and **Pydantic v2** solve this by enforcing mathematical guarantees over LLM outputs.

---

## 1. Why Naive JSON Mode Fails

Many API providers offer `response_format={"type": "json_object"}`. 

While this ensures that the model outputs syntactically valid JSON (braces match), it offers **zero semantic guarantees**:
- Keys may be missing: `{"vuln": "root user"}` instead of `{"finding_id": "...", "severity": "..."}`.
- Types may be wrong: `"severity": 1` instead of `"HIGH"`.
- Nested lists may be malformed or truncated.

---

## 2. The Pydantic v2 Contract

In this platform, domain models are modeled with strict Pydantic v2 validation:

```python
from enum import Enum
from pydantic import BaseModel, Field

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class SecurityFinding(BaseModel):
    finding_id: str = Field(description="Unique identifier e.g. SEC-001")
    title: str = Field(description="Concise description of the vulnerability")
    severity: Severity = Field(description="Categorized severity level")
    file_path: str = Field(description="Relative path to file with issue")
    line_number: int | None = Field(default=None, ge=1, description="Line number where issue occurs")
    evidence: str = Field(description="Exact snippet of offending code or configuration")
    remediation: str = Field(description="Step-by-step instructions to remediate the vulnerability")
    cve_id: str | None = Field(default=None, pattern=r"^CVE-\d{4}-\d{4,}$|^$", description="Associated CVE if any")

class SecurityAuditReport(BaseModel):
    repository_name: str
    compliance_score: float = Field(ge=0.0, le=100.0, description="Overall compliance score 0-100")
    findings: list[SecurityFinding]
    remediation_summary: str
```

---

## 3. How Instructor Works: The Self-Healing Validation Loop

Instructor patches the model client (Google GenAI, Groq, OpenAI, Anthropic). When you call `client.chat.completions.create(response_model=SecurityAuditReport)`:

1. **Schema Injection:** Instructor automatically converts your Pydantic schema into JSON Schema / Tool Call definitions passed to the model.
2. **Extraction & Validation:** Instructor parses the returned JSON into your Pydantic model instance.
3. **The Self-Correction Loop:** If validation fails (e.g. `line_number` was `-5` or `cve_id` did not match regex pattern):
   - Instructor intercepts the `ValidationError`.
   - Instructor automatically issues a **follow-up turn** to the LLM containing the exact error:
     ```text
     "Validation error on field 'cve_id': Value 'cve-2024-invalid' does not match regex.
     Please correct the output."
     ```
   - The model self-corrects and returns the valid object.

```
+---------------------------------------------------------------------------------+
|                        INSTRUCTOR SELF-HEALING LOOP                             |
|                                                                                 |
|   Prompt + Schema ---> [LLM Generation] ---> Raw JSON                           |
|                              ^                     |                            |
|                              |                     v                            |
|                              |            [Pydantic Validation]                 |
|                              |                     |                            |
|                              |              Valid? |                            |
|                              |             /      \                             |
|                              |           No        Yes                          |
|                              |          /            \                          |
|         Re-prompt with ValidationError               [Typed Python Object]      |
+---------------------------------------------------------------------------------+
```

### Example Code:

```python
import instructor
from google import genai
from src.schemas import SecurityAuditReport

# Wrap provider client with instructor
client = instructor.from_gemini(
    client=genai.Client(api_key=os.environ["GEMINI_API_KEY"]),
    mode=instructor.Mode.GEMINI_JSON,
)

# Extract structured object with up to 3 automatic retries
report: SecurityAuditReport = client.chat.completions.create(
    model="gemini-2.0-flash",
    response_model=SecurityAuditReport,
    max_retries=3,
    messages=[
        {"role": "system", "content": "You are a DevSecOps static analysis expert."},
        {"role": "user", "content": f"Analyze these scan results:\n{raw_scan_output}"}
    ],
)

# Access fields directly with full IDE autocomplete and type safety
print(f"Compliance Score: {report.compliance_score}%")
for finding in report.findings:
    print(f"[{finding.severity.value}] {finding.title} in {finding.file_path}")
```

This transforms LLMs from conversational chatbots into **deterministic software components**.
