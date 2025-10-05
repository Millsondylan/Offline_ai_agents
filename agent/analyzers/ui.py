from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .base import Analyzer, AnalyzerResult, CommandResult, build_finding


def _slugify(url: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", url.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60] or "target"


class LighthouseAnalyzer(Analyzer):
    name = "lighthouse"

    def available(self) -> bool:
        return self._which("lighthouse")

    def analyze(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        targets = self.settings.get("targets", [])
        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="no targets configured",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )
        if not self.available():
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="lighthouse not installed",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )

        audits_dir = Path(cycle_dir) / "ui_audits"
        audits_dir.mkdir(parents=True, exist_ok=True)

        flags = self.settings.get("flags", ["--quiet", "--chrome-flags=--headless"])
        if isinstance(flags, str):
            flags = [flags]

        findings = []
        summaries: Dict[str, Dict[str, float]] = {}
        last_command: Optional[CommandResult] = None
        for url in targets:
            slug = _slugify(url)
            base = audits_dir / f"lighthouse-{slug}"
            cmd = [
                "lighthouse",
                url,
                "--output",
                "json",
                "--output",
                "html",
                f"--output-path={base}",
            ] + list(flags)
            result = self._run(cmd, cwd=repo_root, timeout=int(self.settings.get("timeout", 900)))
            last_command = result
            json_path_options = [
                base.with_suffix(".report.json"),
                base.with_suffix(".json"),
            ]
            html_path_options = [
                base.with_suffix(".report.html"),
                base.with_suffix(".html"),
            ]
            json_data = {}
            for candidate in json_path_options:
                if candidate.exists():
                    try:
                        json_data = json.loads(candidate.read_text(encoding="utf-8"))
                        break
                    except json.JSONDecodeError:
                        json_data = {}
            summaries[str(url)] = {}
            categories = json_data.get("categories", {}) if isinstance(json_data, dict) else {}
            for key, entry in categories.items():
                score = entry.get("score") if isinstance(entry, dict) else None
                if isinstance(score, (int, float)):
                    summaries[str(url)][key] = float(score)
                    if key == "accessibility" and score < float(self.settings.get("min_accessibility", 0.9)):
                        findings.append(
                            build_finding(
                                identifier=f"lighthouse::{slug}::{key}",
                                message=f"Accessibility score {score * 100:.0f}%",
                                severity="warning" if score >= 0.7 else "critical",
                                path=url,
                                data={"score": score},
                            )
                        )
            # Ensure HTML file exists (command writes already); if not, create simple stub
            html_written = False
            for candidate in html_path_options:
                if candidate.exists():
                    html_written = True
                    break
            if not html_written:
                html_path = audits_dir / f"lighthouse-{slug}.html"
                html_path.write_text("<html><body><h1>Lighthouse report unavailable</h1></body></html>", encoding="utf-8")

        status = "ok" if not findings else "failed"
        summary = f"audited {len(targets)} targets" + (" - issues found" if findings else "")
        artifacts = {"ui_audits/lighthouse_summary.json": summaries}
        suggestions = []
        if findings:
            suggestions.append("Investigate Lighthouse accessibility scores")
        return AnalyzerResult(
            name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            suggestions=suggestions,
            data={"summaries": summaries},
            artifacts=artifacts,
            command=last_command,
        )


class AxeAnalyzer(Analyzer):
    name = "axe"

    def available(self) -> bool:
        return self._which("axe") or self._which("npx")

    def analyze(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        targets = self.settings.get("targets", [])
        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="no targets configured",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )
        if not self.available():
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="axe CLI not found",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )
        audits_dir = Path(cycle_dir) / "ui_audits"
        audits_dir.mkdir(parents=True, exist_ok=True)
        flags = self.settings.get("flags", [])
        if isinstance(flags, str):
            flags = [flags]

        findings = []
        results: Dict[str, Dict] = {}
        for url in targets:
            slug = _slugify(url)
            out_path = audits_dir / f"axe-{slug}.json"
            if self._which("axe"):
                cmd = ["axe", url, "--save", str(out_path), "--format", "json"] + list(flags)
            else:
                cmd = ["npx", "@axe-core/cli", url, "--save", str(out_path), "--format", "json"] + list(flags)
            result = self._run(cmd, cwd=repo_root, timeout=int(self.settings.get("timeout", 600)))
            try:
                payload = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
            except json.JSONDecodeError:
                payload = {}
            results[url] = payload
            violations = payload.get("violations", []) if isinstance(payload, dict) else []
            for violation in violations:
                if not isinstance(violation, dict):
                    continue
                impact = (violation.get("impact") or "moderate").lower()
                findings.append(
                    build_finding(
                        identifier=f"axe::{violation.get('id', 'rule')}",
                        message=violation.get("description", "axe violation"),
                        severity="critical" if impact in {"critical", "serious"} else "warning",
                        path=url,
                        data={"nodes": len(violation.get('nodes', []))},
                    )
                )
        status = "ok" if not findings else "failed"
        summary = f"axes run on {len(targets)} targets"
        suggestions = []
        if findings:
            suggestions.append("Address axe accessibility violations")
        artifacts = {"ui_audits/axe_summary.json": results}
        return AnalyzerResult(
            name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            suggestions=suggestions,
            data=results,
            artifacts=artifacts,
        )


class Pa11yAnalyzer(Analyzer):
    name = "pa11y"

    def available(self) -> bool:
        return self._which("pa11y")

    def analyze(self, repo_root: str, cycle_dir: str, files: Optional[List[str]] = None) -> AnalyzerResult:
        targets = self.settings.get("targets", [])
        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="no targets configured",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )
        if not self.available():
            return AnalyzerResult(
                name=self.name,
                status="skipped",
                summary="pa11y CLI not found",
                findings=[],
                suggestions=[],
                data={},
                artifacts={},
            )
        audits_dir = Path(cycle_dir) / "ui_audits"
        audits_dir.mkdir(parents=True, exist_ok=True)
        flags = self.settings.get("flags", ["--reporter", "json"])
        if isinstance(flags, str):
            flags = [flags]

        findings = []
        results: Dict[str, Dict] = {}
        for url in targets:
            slug = _slugify(url)
            cmd = ["pa11y", url] + list(flags)
            result = self._run(cmd, cwd=repo_root, timeout=int(self.settings.get("timeout", 600)))
            payload = {}
            try:
                payload = json.loads(result.output)
            except json.JSONDecodeError:
                payload = {"raw": result.output[:2000]}
            results[url] = payload
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    issue_type = item.get("type", "error")
                    severity = "warning" if issue_type == "warning" else "critical"
                    findings.append(
                        build_finding(
                            identifier=f"pa11y::{item.get('code', 'issue')}",
                            message=item.get("message", "pa11y issue"),
                            severity=severity,
                            path=url,
                        )
                    )
        status = "ok" if not findings else "failed"
        summary = f"pa11y reports for {len(targets)} targets"
        artifacts = {"ui_audits/pa11y_summary.json": results}
        suggestions = []
        if findings:
            suggestions.append("Fix pa11y accessibility issues")
        return AnalyzerResult(
            name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            suggestions=suggestions,
            data=results,
            artifacts=artifacts,
        )
