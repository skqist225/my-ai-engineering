"""Node 4: Evaluate Baseline Security Rubrics."""

import re
from src.agent.state import AgentState
from src.extraction.schemas import RubricEvaluation


def evaluate_rubric_node(state: AgentState) -> dict:
    """Evaluate discovered files against baseline security rubrics deterministically."""
    repo_files = state.get("repo_files", {})
    file_contents = state.get("file_contents", {})

    rubric_results: dict[str, list[dict]] = {}

    for repo_name, files in repo_files.items():
        evaluations: list[dict] = []

        # Find dockerfiles
        dockerfiles = [f for f in files if "dockerfile" in f.lower()]
        for df in dockerfiles:
            key = f"{repo_name}/{df}"
            content = file_contents.get(key, "")

            # 1. Non-Root User Check (CIS-DOCKER-4.1)
            has_user = bool(re.search(r"^\s*USER\s+\w+", content, re.MULTILINE | re.IGNORECASE))
            evaluations.append(
                RubricEvaluation(
                    rubric_id="SEC-DOCKER-ROOT",
                    title="Non-Root Container User",
                    status="PASS" if has_user else "FAIL",
                    rule_reference="CIS-DOCKER-4.1",
                    evidence=f"{df}: Contains USER directive" if has_user else f"{df}: Missing USER directive",
                ).model_dump()
            )

            # 2. Latest Tag Check (CIS-DOCKER-4.2)
            has_latest = bool(re.search(r"^\s*FROM\s+[^\s:]+:latest", content, re.MULTILINE | re.IGNORECASE))
            evaluations.append(
                RubricEvaluation(
                    rubric_id="SEC-DOCKER-TAG",
                    title="Immutable Base Image Tag",
                    status="FAIL" if has_latest else "PASS",
                    rule_reference="CIS-DOCKER-4.2",
                    evidence=f"{df}: Uses :latest mutable tag" if has_latest else f"{df}: Pinned image tag",
                ).model_dump()
            )

        # Find Kubernetes manifests
        k8s_files = [f for f in files if f.endswith(".yaml") or f.endswith(".yml")]
        for kf in k8s_files:
            key = f"{repo_name}/{kf}"
            content = file_contents.get(key, "")
            if "kind: Deployment" in content or "kind: Pod" in content:
                # 3. Privileged Container Check (CIS-K8S-5.2.1)
                is_privileged = "privileged: true" in content
                evaluations.append(
                    RubricEvaluation(
                        rubric_id="SEC-K8S-PRIVILEGE",
                        title="Disallow Privileged Containers",
                        status="FAIL" if is_privileged else "PASS",
                        rule_reference="CIS-K8S-5.2.1",
                        evidence=f"{kf}: privileged: true found" if is_privileged else f"{kf}: Not privileged",
                    ).model_dump()
                )

                # 4. Resource Limits (CIS-K8S-5.2.7)
                has_limits = "limits:" in content and "memory:" in content
                evaluations.append(
                    RubricEvaluation(
                        rubric_id="SEC-K8S-RESOURCES",
                        title="Resource Limits Enforced",
                        status="PASS" if has_limits else "WARN",
                        rule_reference="CIS-K8S-5.2.7",
                        evidence=f"{kf}: Memory limits declared" if has_limits else f"{kf}: Missing resource limits",
                    ).model_dump()
                )

        rubric_results[repo_name] = evaluations

    return {"rubric_results": rubric_results}
