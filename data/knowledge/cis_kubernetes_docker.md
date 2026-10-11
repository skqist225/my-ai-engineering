# CIS Benchmarks: Container and Kubernetes Security Guidelines

## 1. Container Image and Runtime Security (CIS Docker Benchmark)

### Rule 4.1: Ensure that a user for the container has been created and set
- **ID:** CIS-DOCKER-4.1
- **Severity:** HIGH
- **Description:** Containers should not run with root (UID 0) privileges. Running as root allows container breakouts to inherit host root privileges.
- **Offending Pattern:** Dockerfiles missing a `USER` directive or explicitly using `USER root`.
- **Remediation:** Create a dedicated system user and group, then switch to it:
  ```dockerfile
  RUN addgroup -S appgroup && adduser -S appuser -G appgroup
  USER appuser
  ```

### Rule 4.2: Ensure that containers use trusted base images and pinned versions
- **ID:** CIS-DOCKER-4.2
- **Severity:** MEDIUM
- **Description:** Mutable tags like `:latest` lead to unpredictable builds and supply chain vulnerability injection.
- **Offending Pattern:** `FROM alpine:latest` or `FROM node:latest`.
- **Remediation:** Pin exact semantic tags or immutable digest hashes:
  ```dockerfile
  FROM alpine:3.19.1@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd49f277b3b5e1d4b
  ```

### Rule 4.6: Ensure HEALTHCHECK instructions have been added to container images
- **ID:** CIS-DOCKER-4.6
- **Severity:** LOW
- **Description:** Images should specify health check probes so orchestrators can detect stalled application processes.
- **Remediation:**
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget --spider -q http://localhost:8080/health || exit 1
  ```

---

## 2. Pod Security Standards (CIS Kubernetes Benchmark)

### Rule 5.2.1: Minimize the admission of privileged containers
- **ID:** CIS-K8S-5.2.1
- **Severity:** CRITICAL
- **Description:** Privileged containers have root capabilities over host devices and kernel parameters.
- **Offending Pattern:** `securityContext.privileged: true` in Pod or Container specs.
- **Remediation:** Set `securityContext.privileged: false` or omit the flag.

### Rule 5.2.2: Ensure containers do not admit privilege escalation
- **ID:** CIS-K8S-5.2.2
- **Severity:** HIGH
- **Description:** A process can gain more privileges than its parent process via setuid/setgid binaries.
- **Remediation:**
  ```yaml
  securityContext:
    allowPrivilegeEscalation: false
  ```

### Rule 5.2.3: Ensure containers run with read-only root filesystems
- **ID:** CIS-K8S-5.2.3
- **Severity:** MEDIUM
- **Description:** Prevents attackers from writing binaries or mutating system libraries inside a running container.
- **Remediation:**
  ```yaml
  securityContext:
    readOnlyRootFilesystem: true
  ```
  Mount writable temporary directories using `emptyDir` volumes at `/tmp` or `/app/cache`.

### Rule 5.2.6: Ensure default capabilities are dropped
- **ID:** CIS-K8S-5.2.6
- **Severity:** HIGH
- **Description:** Linux capabilities provide fine-grained superuser privileges. All default capabilities should be dropped.
- **Remediation:**
  ```yaml
  securityContext:
    capabilities:
      drop:
        - ALL
      add:
        - NET_BIND_SERVICE # Only if binding ports < 1024
  ```

### Rule 5.2.7: Ensure memory and CPU limits are set
- **ID:** CIS-K8S-5.2.7
- **Severity:** MEDIUM
- **Description:** Containers without resource limits can cause Denial of Service (DoS) by starving sibling workloads on the node.
- **Remediation:**
  ```yaml
  resources:
    limits:
      cpu: "500m"
      memory: "512Mi"
    requests:
      cpu: "100m"
      memory: "128Mi"
  ```
