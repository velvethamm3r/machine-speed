#!/usr/bin/env python3
"""One-off: add the initial topic tags and corrections log to data.json.

Use this only if data.json has moved on since 2026-09-26 (a daily run landed
before this upload), so the data.json in the upload would overwrite newer
items. Run from the repo root:

    python3 tools/apply_findings_tags.py

It edits data.json in place, touching only `topics` on the listed items, any
leftover `threads` tags (replaced by topics), `topic` and `items` on watchlist threads,
and the `corrections` list. It is
safe to run twice. Delete it afterwards.
"""
import json
from pathlib import Path

TOPICS = {
 "cisa-kev-langflow-cve-2026-9198-exploited": [
  "attacks-on-ai"
 ],
 "wiz-ai-infrastructure-honeypot-attacks": [
  "attacks-on-ai"
 ],
 "talos-uat-10147-agentic-ai-post-compromise": [
  "ai-in-attacks"
 ],
 "nvidia-hugging-face-reported-acquisition": [
  "evaluation-incidents"
 ],
 "alabama-ag-openai-hugging-face-investigation-subpoena": [
  "evaluation-incidents"
 ],
 "cosnitch-copilot-personal-one-click-exfiltration": [
  "attacks-on-ai"
 ],
 "mlflow-ssrf-cve-2026-64849-exploited": [
  "attacks-on-ai"
 ],
 "asecurity-zoomsday-ai-zoom-rce": [
  "ai-found-vulnerabilities"
 ],
 "zai-glm-5-3-cyber-benchmarks": [
  "frontier-capability"
 ],
 "taiwan-ai-agent-government-attack": [
  "ai-in-attacks"
 ],
 "rapid7-ai-assisted-sharepoint-rce-chain": [
  "ai-found-vulnerabilities"
 ],
 "pillar-google-adk-agent-to-agent-injection": [
  "attacks-on-ai"
 ],
 "trellix-underground-ai-offensive-tools": [
  "ai-in-attacks"
 ],
 "house-democrats-anthropic-eval-oversight-letter": [
  "evaluation-incidents"
 ],
 "sanders-ai-development-pause-letter": [
  "evaluation-incidents"
 ],
 "msft-mai-cyber-flash": [
  "frontier-capability"
 ],
 "aisi-eval-cheating": [
  "frontier-capability"
 ],
 "kimi-k3-joint-eval": [
  "frontier-capability"
 ],
 "openai-exploitgym": [
  "evaluation-incidents"
 ],
 "sakana-fugu-cyber": [
  "frontier-capability"
 ],
 "hf-llm-forensics": [
  "evaluation-incidents",
  "frontier-capability"
 ],
 "hermes-thai-finance": [
  "ai-in-attacks"
 ],
 "agentforger": [
  "attacks-on-ai"
 ],
 "jadepuffer-encforge": [
  "ai-in-attacks"
 ],
 "iran-plc": [
  "critical-infrastructure"
 ],
 "fakegit": [
  "attacks-on-ai"
 ],
 "public-cyber-benchmarks-saturating-faster-than-model-capability": [
  "frontier-capability"
 ],
 "openai-gpt5-6-high-cybersecurity-capability-designation": [
  "frontier-capability"
 ],
 "meta-muse-spark-11-cyber-high-risk-not-ruled-out": [
  "frontier-capability"
 ],
 "xbow-cross-model-offensive-security-cost-comparison": [
  "frontier-capability"
 ],
 "secrespond-post-compromise-incident-response-benchmark": [
  "frontier-capability"
 ],
 "anthropic-claude-models-breached-real-systems-in-evals": [
  "evaluation-incidents"
 ],
 "openai-third-party-cyber-evaluations-disclosure": [
  "evaluation-incidents"
 ],
 "microsoft-ai-discovery-patch-volume": [
  "ai-found-vulnerabilities"
 ],
 "aisi-unsanctioned-agent-actions": [
  "evaluation-incidents"
 ],
 "crs-in-focus-executive-order-14409-explained": [
  "frontier-capability"
 ],
 "white-house-gold-eagle-ai-vulnerability-clearinghouse": [
  "ai-found-vulnerabilities"
 ],
 "oncd-cairncross-black-hat-open-source-ai-and-no-regulatory-regime": [
  "frontier-capability"
 ],
 "orca-state-of-ai-security-unpatched-ai-packages": [
  "attacks-on-ai"
 ],
 "microsoft-patch-tuesday-record-ai-copilot-cves": [
  "ai-found-vulnerabilities"
 ],
 "terraform-mcp-server-cross-tenant-credential-reuse-patch": [
  "attacks-on-ai"
 ],
 "microsoft-defender-prompt-injection-protection-preview": [
  "attacks-on-ai"
 ],
 "cisa-open-source-software-security-practices-ai-provenance": [
  "frontier-capability",
  "attacks-on-ai"
 ],
 "jadepuffer-agentic-ransomware-langflow": [
  "ai-in-attacks"
 ],
 "indirect-prompt-injection-web-content-browsing-agents": [
  "attacks-on-ai"
 ],
 "china-linked-operators-claude-code-deepseek-government-intrusions": [
  "ai-in-attacks"
 ],
 "unit42-deepseek-hermes-agent-autonomous-attacks": [
  "ai-in-attacks"
 ],
 "fbi-epa-alert-water-wastewater-plc-targeting": [
  "critical-infrastructure"
 ],
 "keyv-npm-worm-claude-code-hook-persistence": [
  "attacks-on-ai"
 ],
 "portswigger-http-terminator-ai-novel-desync": [
  "ai-found-vulnerabilities"
 ],
 "off-by-1-labs-ai-generated-patches-mostly-broken": [
  "ai-found-vulnerabilities"
 ],
 "okta-gray-market-frontier-model-access-proxies": [
  "attacks-on-ai"
 ],
 "crowdstrike-2026-threat-hunting-report-ai-embedded": [
  "ai-in-attacks"
 ],
 "openai-astra-critical-cyber-delay": [
  "frontier-capability"
 ],
 "openai-daybreak-gpt56-cyber-gated-defenders": [
  "frontier-capability"
 ],
 "vulncheck-1h-2026-ai-vuln-exploitation-rate": [
  "ai-found-vulnerabilities"
 ],
 "openclaw-gym-booking-agent-autonomous-exploit": [
  "ai-in-attacks"
 ],
 "cisa-nsa-fbi-siemens-s7-ai-generated-exploit-scripts": [
  "critical-infrastructure"
 ],
 "cisa-kev-ray-ai-framework-cve-2025-62593-exploited": [
  "attacks-on-ai"
 ],
 "rapid7-operation-asterix-claude-code-crypto-vishing": [
  "ai-in-attacks"
 ],
 "google-mandiant-avdh-agentic-vuln-discovery": [
  "ai-found-vulnerabilities"
 ],
 "openai-preparedness-framework-rewrite-frontier-rl-hold": [
  "frontier-capability"
 ],
 "rovoblast-atlassian-rovo-prompt-injection-exfiltration": [
  "attacks-on-ai"
 ],
 "adversa-cryptographic-context-injection-grok-gemini": [
  "attacks-on-ai"
 ],
 "state-ags-openai-preservation-demand": [
  "evaluation-incidents"
 ],
 "guidelight-frontier-lab-rogue-model-containment-scorecard": [
  "evaluation-incidents"
 ],
 "anthropic-mythos-5-defender-access-fund": [
  "frontier-capability"
 ],
 "aikido-open-weight-vuln-discovery-benchmark": [
  "frontier-capability"
 ],
 "uk-ncsc-agentic-ai-interim-guidance": [
  "ai-in-attacks"
 ],
 "nemoclaw-ollama-dns-rebinding-model-poisoning": [
  "attacks-on-ai"
 ],
 "toxnetv2-linux-botnet-llm-attack-commands": [
  "ai-in-attacks"
 ],
 "redc2-npm-llm-operated-c2": [
  "attacks-on-ai"
 ],
 "unit42-nova-vulnerability-burst": [
  "ai-found-vulnerabilities"
 ],
 "unit42-perturbation-probing-safety-neurons": [
  "attacks-on-ai"
 ],
 "gambit-aurora-ransomware-cursor-agent": [
  "ai-in-attacks"
 ],
 "cisa-kev-artifactory-linux-kernel-openai-agent-flaws": [
  "evaluation-incidents"
 ],
 "metr-redwood-eval-agent-coordination-investigation": [
  "evaluation-incidents"
 ],
 "microsoft-ai-gateway-orchestration-intrusions": [
  "attacks-on-ai"
 ],
 "fbi-nsa-cnmf-qtfy-ai-integration-advisory": [
  "ai-in-attacks"
 ],
 "metr-discovery-versus-exploitation-rates": [
  "ai-found-vulnerabilities"
 ],
 "meta-model-exploited-flaw-in-irregular-evaluation": [
  "evaluation-incidents"
 ],
 "ncsc-statement-frontier-ai-evaluation-incidents": [
  "evaluation-incidents"
 ],
 "aisi-open-weight-cyber-gap-four-to-seven-months": [
  "frontier-capability"
 ],
 "metasploit-langflow-flowise-ai-platform-modules": [
  "attacks-on-ai"
 ],
 "arxiv-ctf-abacus-flag-provenance-audit": [
  "frontier-capability"
 ],
 "anthropic-august-risk-report-misalignment-low": [
  "evaluation-incidents"
 ],
 "gemini-3-7-flash-cyber-alert-threshold": [
  "frontier-capability"
 ],
 "nist-nvd-modernization-ai-rfi": [
  "ai-found-vulnerabilities"
 ],
 "aisi-control-red-team-monitor-vulnerabilities": [
  "attacks-on-ai"
 ],
 "anthropic-alignment-security-remediation": [
  "evaluation-incidents"
 ],
 "eset-guardbreaker-llm-guardrail-malware": [
  "attacks-on-ai"
 ],
 "anthropic-infostealer-claude-session-hijacking": [
  "attacks-on-ai"
 ],
 "vulncheck-langflow-mass-exploitation": [
  "attacks-on-ai"
 ],
 "epoch-july-cve-severity-spike": [
  "ai-found-vulnerabilities"
 ],
 "crowdstrike-cybench-benchmark-cheating": [
  "frontier-capability"
 ],
 "trellix-clawhub-malicious-skills": [
  "attacks-on-ai"
 ],
 "unit42-ai-token-jacking": [
  "attacks-on-ai"
 ],
 "senate-ai-model-access-framework-letter": [
  "frontier-capability",
  "attacks-on-ai"
 ],
 "nist-nccoe-agentic-ai-identity": [
  "ai-in-attacks"
 ],
 "rand-model-weight-security-sl3": [
  "attacks-on-ai"
 ],
 "cisco-model-provenance-entanglement": [
  "frontier-capability"
 ],
 "servicenow-ai-platform-critical-flaws": [
  "attacks-on-ai"
 ],
 "arxiv-cot-monitor-collapse": [
  "attacks-on-ai"
 ],
 "arxiv-autobypass-endpoint-evasion": [
  "attacks-on-ai"
 ],
 "wiz-red-agent-snowflake-ci-injection": [
  "ai-found-vulnerabilities"
 ],
 "openai-astra-critical-cyber": [
  "frontier-capability"
 ],
 "anthropic-mythos-5-1-system-card": [
  "frontier-capability"
 ],
 "anthropic-fable-mythos-5-1-access": [
  "frontier-capability"
 ],
 "metr-own-security-incidents": [
  "attacks-on-ai"
 ],
 "xai-grok-4-6-cyber-scores": [
  "frontier-capability"
 ],
 "dreadnode-every-model-cheats": [
  "frontier-capability"
 ],
 "vulncheck-ai-poc-flood": [
  "ai-found-vulnerabilities"
 ],
 "rapid7-q2-2026-cve-doubling": [
  "ai-found-vulnerabilities"
 ],
 "pillar-gemini-cli-gcp-compromise": [
  "attacks-on-ai"
 ],
 "adversa-skill-scanner-bypass": [
  "attacks-on-ai"
 ],
 "eset-h1-2026-agent-skills": [
  "attacks-on-ai"
 ],
 "wiz-rust-arrayref-supply-chain": [
  "attacks-on-ai"
 ],
 "csis-iran-water-mapping": [
  "critical-infrastructure"
 ],
 "sharepoint-agent-found-flaw-exploited": [
  "ai-found-vulnerabilities"
 ],
 "sbom-minimum-elements-2026": [
  "attacks-on-ai"
 ],
 "blade-act-model-extraction": [
  "attacks-on-ai"
 ],
 "nist-sp-800-239-ai-datacenter": [
  "attacks-on-ai"
 ],
 "mandiant-oss-supply-chain-guidance": [
  "attacks-on-ai"
 ],
 "varonis-dialogflow-rogue-agent": [
  "attacks-on-ai"
 ],
 "sre-bench-reverse-engineering": [
  "frontier-capability"
 ],
 "google-gemini-3-8-flash-cyber": [
  "frontier-capability"
 ],
 "google-fairwind-program": [
  "frontier-capability"
 ],
 "unit42-ai-assisted-intrusion-ten-hours": [
  "ai-in-attacks"
 ],
 "cisa-kev-litellm-mcp-auth-bypass": [
  "attacks-on-ai"
 ],
 "manifold-gitspawn-agent-git-config-execution": [
  "attacks-on-ai"
 ],
 "pillar-grafana-mcp-session-spoofing-ssrf": [
  "attacks-on-ai"
 ],
 "arxiv-skillshift-covert-policy-steering": [
  "attacks-on-ai"
 ],
 "owasp-agent-control-standard-donation": [
  "attacks-on-ai"
 ],
 "xbow-bing-images-autonomous-rce": [
  "ai-found-vulnerabilities"
 ],
 "cve-program-frontier-ai-cna-pilot": [
  "ai-found-vulnerabilities"
 ],
 "project-watershed-250-texas-water": [
  "critical-infrastructure"
 ],
 "tenet-ghostjacking-log-prompt-injection": [
  "attacks-on-ai"
 ],
 "hiddenlayer-claude-code-skill-frontmatter": [
  "attacks-on-ai"
 ],
 "pillar-deadbugz-mcp-supply-chain": [
  "attacks-on-ai"
 ],
 "vulncheck-langflow-ai-stack-exploitation": [
  "attacks-on-ai"
 ],
 "irregular-kimi-k3-first-open-weight-solve": [
  "frontier-capability"
 ],
 "dreadnode-airtbench-open-weight-parity": [
  "frontier-capability"
 ],
 "dreadnode-scopejudge-offensive-agent-gating": [
  "attacks-on-ai"
 ],
 "deepmind-double-blind-evaluation-pilot": [
  "evaluation-incidents"
 ],
 "beazley-security-q2-vulnerability-surge": [
  "ai-found-vulnerabilities"
 ],
 "crowdstrike-safemind-red-tempest-blue-solano": [
  "frontier-capability"
 ],
 "nvidia-hugging-face-definitive-agreement": [
  "evaluation-incidents"
 ],
 "reuters-dsewiki-openai-agent-breakout": [
  "evaluation-incidents"
 ],
 "openai-gpt6-astra-safety-overview-monitorability": [
  "frontier-capability"
 ],
 "unit42-latam-commercial-llm-assisted-intrusions": [
  "ai-in-attacks"
 ],
 "microsoft-ascii-smuggling-phishing-filter-evasion": [
  "attacks-on-ai"
 ],
 "pillar-ai-coding-agent-sandbox-escapes": [
  "attacks-on-ai"
 ],
 "boozallen-cyber-weapon-index": [
  "frontier-capability"
 ],
 "boozallen-vellox-guile-counter-ai": [
  "ai-in-attacks"
 ],
 "echo-mythos-readiness-unreviewed-findings": [
  "ai-found-vulnerabilities"
 ],
 "greynoise-fake-ai-crawler-credential-scanning": [
  "attacks-on-ai"
 ],
 "openai-alien-mind-superhuman-intrusion": [
  "frontier-capability"
 ],
 "openai-research-acceleration-container-shutdown": [
  "evaluation-incidents"
 ],
 "openai-misalignment-disclosure-standard": [
  "evaluation-incidents"
 ],
 "nightmare-eclipse-endpoint-zero-day-pocs": [
  "attacks-on-ai"
 ],
 "nsa-cisa-fbi-china-ai-distillation-advisory": [
  "attacks-on-ai"
 ],
 "gtig-autonomous-multi-agent-credential-harvest": [
  "ai-in-attacks"
 ],
 "gtig-unc6508-local-llm-victim-compute": [
  "frontier-capability",
  "ai-in-attacks"
 ],
 "calif-weworm-wechat-zero-click": [
  "ai-found-vulnerabilities"
 ],
 "microsoft-september-2026-patch-tuesday-record": [
  "ai-found-vulnerabilities"
 ],
 "anthropic-alignment-assessment-four-incidents": [
  "evaluation-incidents"
 ],
 "greynoise-papercut-ai-orchestrated-campaign": [
  "ai-in-attacks"
 ],
 "anthropic-misuse-report-september-2026": [
  "ai-in-attacks"
 ],
 "anthropic-gtg50020-eval-sandbox-api-keys": [
  "evaluation-incidents",
  "attacks-on-ai"
 ],
 "hawley-openai-hugging-face-investigation": [
  "evaluation-incidents"
 ],
 "openai-agents-additional-coordination-sites": [
  "evaluation-incidents"
 ],
 "openai-agents-rubygems-may-campaign": [
  "evaluation-incidents"
 ],
 "gitlab-duo-chat-credential-flaw-probes": [
  "attacks-on-ai"
 ],
 "deepmind-agent-swarm-cheating-whistleblowing": [
  "evaluation-incidents"
 ],
 "amodei-pace-the-frontier-botnet-warning": [
  "frontier-capability"
 ],
 "senate-frontier-ai-duty-of-care-negotiations": [
  "evaluation-incidents"
 ],
 "anthropic-gtg10007-autonomous-vulnerability-research": [
  "ai-in-attacks"
 ],
 "anthropic-seven-china-labs-distillation": [
  "attacks-on-ai"
 ],
 "sglang-safeunpickler-bypass-cve-2026-86793": [
  "attacks-on-ai"
 ],
 "china-mss-chen-yixin-frontier-model-cyber-warning": [
  "frontier-capability"
 ],
 "stop-rogue-ai-act-agent-inventory-standards": [
  "ai-in-attacks"
 ],
 "checkpoint-chatgpt-cross-account-artifactory-channel": [
  "attacks-on-ai"
 ],
 "checkpoint-puzzlemask-gatekeeper-bypass": [
  "attacks-on-ai"
 ],
 "deepseek-harness-sandbox-escape-cve-2026-82533": [
  "attacks-on-ai"
 ],
 "exposed-self-hosted-ai-endpoints-census": [
  "attacks-on-ai"
 ],
 "sophos-luciferus-uncensored-ai-subscription": [
  "ai-in-attacks"
 ],
 "peoples-daily-rejects-us-distillation-claims": [
  "attacks-on-ai"
 ],
 "von-der-leyen-soteu-ai-hacking-warning": [
  "frontier-capability"
 ],
 "openai-model-misalignment-reporting-framework": [
  "evaluation-incidents"
 ],
 "openai-agents-hugging-face-may-precursor": [
  "evaluation-incidents"
 ],
 "aepd-first-notified-ai-agent-executed-breach": [
  "ai-in-attacks"
 ],
 "cisco-ise-hardening-frontier-ai-discovery": [
  "ai-found-vulnerabilities"
 ],
 "cisco-ise-auth-bypass-actively-exploited": [
  "ai-found-vulnerabilities"
 ],
 "air-security-plugin4shell-agent-plugin-marketplaces": [
  "attacks-on-ai"
 ],
 "irregular-agentic-self-modification-open-weights": [
  "frontier-capability",
  "attacks-on-ai"
 ],
 "hush-security-mcp-config-hardcoded-credentials": [
  "attacks-on-ai"
 ],
 "hacktron-claude-opus-5-openai-monorepo-access": [
  "frontier-capability"
 ],
 "google-gemini-irregular-eval-three-companies": [
  "evaluation-incidents"
 ],
 "california-eo-n-9-26-ai-kill-switch-onsite-verification": [
  "evaluation-incidents"
 ],
 "crowdstrike-phantomraven-llm-written-npm-stealer": [
  "attacks-on-ai"
 ],
 "anthropic-opus-5-5-cyber-request-routing": [
  "frontier-capability"
 ],
 "talos-closedquorum-autonomous-ai-c2-implant": [
  "ai-in-attacks"
 ],
 "talos-cairn-ai-integrated-malware-framework": [
  "ai-in-attacks"
 ],
 "microsoft-dcu-eviltokens-disruption": [
  "ai-in-attacks"
 ],
 "colorado-water-utilities-ot-intrusions": [
  "critical-infrastructure"
 ],
 "openai-agent-services-australia-medicare-portal": [
  "evaluation-incidents"
 ],
 "california-ai-eo-independent-expert-panel": [
  "evaluation-incidents"
 ],
 "oregon-executive-order-26-26-ai-procurement": [
  "evaluation-incidents"
 ],
 "team-cymru-llm-relay-transfer-stations": [
  "attacks-on-ai"
 ],
 "gambit-ai-agent-skimming-campaign": [
  "ai-in-attacks"
 ],
 "irregular-eval-incidents-postmortem": [
  "evaluation-incidents"
 ],
 "openai-agent-user-images-misalignment-disclosure": [
  "evaluation-incidents"
 ],
 "microsoft-storm-3168-azure-service-principals": [
  "ai-in-attacks"
 ],
 "carbonato-docker-botnet-hermes-agent": [
  "ai-in-attacks",
  "attacks-on-ai"
 ],
 "memtensor-sckit-supply-chain-worm": [
  "attacks-on-ai"
 ],
 "bragjack-browser-agent-prompt-forcing": [
  "attacks-on-ai"
 ],
 "cisa-fbi-third-party-ics-integrator-considerations": [
  "critical-infrastructure"
 ],
 "spycloud-water-utility-infostealer-exposure": [
  "critical-infrastructure"
 ]
}

CORRECTIONS = [
 {
  "date": "2026-08-12",
  "item": "openai-astra-critical-cyber-delay",
  "text": "Date corrected from Aug 10 to Aug 7, the date of OpenAI's own post, and the headline and summary softened to match it: the primary describes pausing internal Astra work that does not meet strengthened security controls, not a public release delay. Source moved from Axios to OpenAI."
 },
 {
  "date": "2026-08-12",
  "item": "openai-daybreak-gpt56-cyber-gated-defenders",
  "text": "Re-checked against OpenAI's own post. A press-only partner count and list, and a characterisation that partners received findings rather than the models, were removed as unsupported by the primary, which names three partners receiving model access."
 },
 {
  "date": "2026-08-24",
  "item": "google-mandiant-avdh-agentic-vuln-discovery",
  "text": "Date corrected from Aug 19 to Aug 18, the date of Google's own post, and a press figure for the number of pipeline stages replaced with the primary's description. Source moved from Help Net Security to Mandiant/GTIG."
 },
 {
  "date": "2026-08-24",
  "item": "cisa-kev-ray-ai-framework-cve-2025-62593-exploited",
  "text": "A sentence tying this CVE to Oligo Security's ShadowRay 2.0 campaign was removed. ShadowRay 2.0 exploits a different, older Ray flaw (CVE-2023-48022); the sources do not link the two. Source moved from press to the NIST NVD record."
 }
]

WATCH_TOPICS = {
 "Evals as attack surface": "evaluation-incidents",
 "Government response to the eval incidents": "evaluation-incidents",
 "HF breach open threads": "evaluation-incidents",
 "Frontier cyber thresholds crossed": "frontier-capability",
 "Vendor benchmark claims": "frontier-capability",
 "Open-weight cyber gap": "frontier-capability",
 "Gated model access": "frontier-capability",
 "Agent-abuse attack surface": "ai-in-attacks",
 "Assistant prompt-injection exfiltration": "attacks-on-ai",
 "Agent supply chain": "attacks-on-ai",
 "AI infrastructure as attack surface": "attacks-on-ai",
 "Defeating the AI defender": "attacks-on-ai",
 "Model-access abuse": "attacks-on-ai",
 "Distillation as exfiltration": "attacks-on-ai",
 "Vulnerability disclosure at machine speed": "ai-found-vulnerabilities",
 "Water-sector control systems": "critical-infrastructure"
}

WATCH_ITEMS = {
 "Evals as attack surface": [
  "openai-agent-user-images-misalignment-disclosure",
  "openai-agent-services-australia-medicare-portal",
  "oregon-executive-order-26-26-ai-procurement",
  "california-ai-eo-independent-expert-panel",
  "california-eo-n-9-26-ai-kill-switch-onsite-verification",
  "google-gemini-irregular-eval-three-companies",
  "openai-model-misalignment-reporting-framework",
  "openai-agents-hugging-face-may-precursor",
  "openai-agents-rubygems-may-campaign",
  "hawley-openai-hugging-face-investigation",
  "anthropic-gtg50020-eval-sandbox-api-keys",
  "openai-agents-additional-coordination-sites",
  "anthropic-alignment-assessment-four-incidents",
  "openai-research-acceleration-container-shutdown",
  "openai-misalignment-disclosure-standard",
  "reuters-dsewiki-openai-agent-breakout",
  "deepmind-agent-swarm-cheating-whistleblowing",
  "anthropic-alignment-security-remediation",
  "deepmind-double-blind-evaluation-pilot",
  "cisa-kev-artifactory-linux-kernel-openai-agent-flaws",
  "metr-redwood-eval-agent-coordination-investigation",
  "alabama-ag-openai-hugging-face-investigation-subpoena",
  "irregular-eval-incidents-postmortem",
  "anthropic-august-risk-report-misalignment-low",
  "house-democrats-anthropic-eval-oversight-letter",
  "sanders-ai-development-pause-letter",
  "meta-model-exploited-flaw-in-irregular-evaluation",
  "aisi-unsanctioned-agent-actions",
  "openai-third-party-cyber-evaluations-disclosure",
  "ncsc-statement-frontier-ai-evaluation-incidents",
  "state-ags-openai-preservation-demand",
  "anthropic-claude-models-breached-real-systems-in-evals",
  "openai-exploitgym"
 ],
 "Government response to the eval incidents": [
  "california-ai-eo-independent-expert-panel",
  "oregon-executive-order-26-26-ai-procurement",
  "california-eo-n-9-26-ai-kill-switch-onsite-verification",
  "senate-frontier-ai-duty-of-care-negotiations",
  "hawley-openai-hugging-face-investigation",
  "alabama-ag-openai-hugging-face-investigation-subpoena",
  "guidelight-frontier-lab-rogue-model-containment-scorecard",
  "sanders-ai-development-pause-letter",
  "house-democrats-anthropic-eval-oversight-letter",
  "ncsc-statement-frontier-ai-evaluation-incidents",
  "state-ags-openai-preservation-demand"
 ],
 "Agent-abuse attack surface": [
  "microsoft-storm-3168-azure-service-principals",
  "carbonato-docker-botnet-hermes-agent",
  "gambit-ai-agent-skimming-campaign",
  "talos-closedquorum-autonomous-ai-c2-implant",
  "microsoft-dcu-eviltokens-disruption",
  "talos-cairn-ai-integrated-malware-framework",
  "sophos-luciferus-uncensored-ai-subscription",
  "aepd-first-notified-ai-agent-executed-breach",
  "anthropic-misuse-report-september-2026",
  "anthropic-gtg10007-autonomous-vulnerability-research",
  "greynoise-papercut-ai-orchestrated-campaign",
  "stop-rogue-ai-act-agent-inventory-standards",
  "gtig-unc6508-local-llm-victim-compute",
  "gtig-autonomous-multi-agent-credential-harvest",
  "unit42-latam-commercial-llm-assisted-intrusions",
  "unit42-ai-assisted-intrusion-ten-hours",
  "boozallen-vellox-guile-counter-ai",
  "gambit-aurora-ransomware-cursor-agent",
  "nist-nccoe-agentic-ai-identity",
  "fbi-nsa-cnmf-qtfy-ai-integration-advisory",
  "toxnetv2-linux-botnet-llm-attack-commands",
  "talos-uat-10147-agentic-ai-post-compromise",
  "uk-ncsc-agentic-ai-interim-guidance",
  "rapid7-operation-asterix-claude-code-crypto-vishing",
  "taiwan-ai-agent-government-attack",
  "trellix-underground-ai-offensive-tools",
  "openclaw-gym-booking-agent-autonomous-exploit",
  "crowdstrike-2026-threat-hunting-report-ai-embedded",
  "unit42-deepseek-hermes-agent-autonomous-attacks",
  "hermes-thai-finance",
  "jadepuffer-encforge",
  "china-linked-operators-claude-code-deepseek-government-intrusions",
  "jadepuffer-agentic-ransomware-langflow"
 ],
 "Assistant prompt-injection exfiltration": [
  "bragjack-browser-agent-prompt-forcing",
  "checkpoint-chatgpt-cross-account-artifactory-channel",
  "microsoft-ascii-smuggling-phishing-filter-evasion",
  "adversa-cryptographic-context-injection-grok-gemini",
  "cosnitch-copilot-personal-one-click-exfiltration",
  "rovoblast-atlassian-rovo-prompt-injection-exfiltration",
  "microsoft-defender-prompt-injection-protection-preview",
  "agentforger",
  "varonis-dialogflow-rogue-agent",
  "indirect-prompt-injection-web-content-browsing-agents"
 ],
 "Agent supply chain": [
  "memtensor-sckit-supply-chain-worm",
  "crowdstrike-phantomraven-llm-written-npm-stealer",
  "air-security-plugin4shell-agent-plugin-marketplaces",
  "arxiv-skillshift-covert-policy-steering",
  "manifold-gitspawn-agent-git-config-execution",
  "owasp-agent-control-standard-donation",
  "redc2-npm-llm-operated-c2",
  "wiz-rust-arrayref-supply-chain",
  "trellix-clawhub-malicious-skills",
  "pillar-gemini-cli-gcp-compromise",
  "pillar-deadbugz-mcp-supply-chain",
  "tenet-ghostjacking-log-prompt-injection",
  "keyv-npm-worm-claude-code-hook-persistence",
  "pillar-google-adk-agent-to-agent-injection",
  "cisa-open-source-software-security-practices-ai-provenance",
  "mandiant-oss-supply-chain-guidance",
  "adversa-skill-scanner-bypass",
  "sbom-minimum-elements-2026",
  "fakegit",
  "pillar-ai-coding-agent-sandbox-escapes",
  "hiddenlayer-claude-code-skill-frontmatter",
  "eset-h1-2026-agent-skills"
 ],
 "Tracked bills": [
  "ai-cyber-defense-act-hr-10519",
  "guthrie-frontier-act-vote-slips-to-2027",
  "senate-frontier-ai-duty-of-care-negotiations",
  "stop-rogue-ai-act-agent-inventory-standards",
  "ban-artificial-superintelligence-act",
  "hr6500-cisa-2015-sunset-extension",
  "self-improving-ai-monitoring-act",
  "blade-act-model-extraction",
  "frontier-act-oversight",
  "cats-act",
  "ai-kill-switch-act",
  "warner-secure-ai-development-act-s5061"
 ],
 "Industry-government defense collaboration": [
  "openai-daybreak-ukraine-civilian-defense",
  "ai-cyber-defense-act-hr-10519",
  "cis-openai-ai-cyber-defense-pilot-sltt",
  "openai-daybreak-frontline-defenders-1b",
  "sentinelone-wayfinder-daybreak-gpt56-cyber",
  "google-fairwind-program",
  "openai-collective-cyber-defense-open-letter",
  "anthropic-mythos-5-defender-access-fund",
  "whitehouse-transnational-cyber-crime-private-sector-operations-memo",
  "openai-daybreak-gpt56-cyber-gated-defenders",
  "osaa-safe-incident-sharing-rfc",
  "nvidia-openshell-agent-sandbox-runtime",
  "cve-program-frontier-ai-cna-pilot",
  "open-secure-ai-alliance",
  "white-house-gold-eagle-ai-vulnerability-clearinghouse",
  "uk-ncsc-cyber-shield-agentic-defence",
  "cisa-anthropic-mythos-federal-code-audit"
 ],
 "Open-weight cyber gap": [
  "irregular-agentic-self-modification-open-weights",
  "gtig-unc6508-local-llm-victim-compute",
  "cisco-model-provenance-entanglement",
  "aikido-open-weight-vuln-discovery-benchmark",
  "irregular-kimi-k3-first-open-weight-solve",
  "zai-glm-5-3-cyber-benchmarks",
  "oncd-cairncross-black-hat-open-source-ai-and-no-regulatory-regime",
  "cisa-open-source-software-security-practices-ai-provenance",
  "dreadnode-airtbench-open-weight-parity",
  "kimi-k3-joint-eval",
  "aisi-open-weight-cyber-gap-four-to-seven-months",
  "hf-llm-forensics",
  "xbow-cross-model-offensive-security-cost-comparison"
 ],
 "Vendor benchmark claims": [
  "boozallen-cyber-weapon-index",
  "crowdstrike-safemind-red-tempest-blue-solano",
  "arxiv-ctf-abacus-flag-provenance-audit",
  "aikido-open-weight-vuln-discovery-benchmark",
  "crowdstrike-cybench-benchmark-cheating",
  "zai-glm-5-3-cyber-benchmarks",
  "xai-grok-4-6-cyber-scores",
  "sre-bench-reverse-engineering",
  "dreadnode-every-model-cheats",
  "secrespond-post-compromise-incident-response-benchmark",
  "msft-mai-cyber-flash",
  "sakana-fugu-cyber",
  "aisi-eval-cheating",
  "xbow-cross-model-offensive-security-cost-comparison",
  "public-cyber-benchmarks-saturating-faster-than-model-capability"
 ],
 "EU implementation timeline": [
  "enisa-threat-landscape-2026",
  "von-der-leyen-soteu-ai-hacking-warning",
  "aisle-enisa-cra-reporting-platform-ai-code-review",
  "esas-frontier-ai-ict-risk-supervisory-statement",
  "eu-ai-act-transparency-rules-enforcement-begins",
  "enisa-frontier-ai-era-cybersecurity",
  "eu-action-plan-cybersecurity-and-artificial-intelligence",
  "ecb-ai-cyber-action-plans-banks"
 ],
 "Water-sector control systems": [
  "cisa-fbi-third-party-ics-integrator-considerations",
  "spycloud-water-utility-infostealer-exposure",
  "colorado-water-utilities-ot-intrusions",
  "project-watershed-250-texas-water",
  "cisa-nsa-fbi-siemens-s7-ai-generated-exploit-scripts",
  "csis-iran-water-mapping",
  "fbi-epa-alert-water-wastewater-plc-targeting",
  "iran-plc"
 ],
 "CAISI leadership and output": [
  "self-improving-ai-monitoring-act",
  "nist-doe-genesis-mission-ai-critical-infrastructure-security-center",
  "kimi-k3-joint-eval",
  "caisi-raman"
 ],
 "HF breach open threads": [
  "california-eo-n-9-26-ai-kill-switch-onsite-verification",
  "openai-agents-hugging-face-may-precursor",
  "hawley-openai-hugging-face-investigation",
  "openai-agents-additional-coordination-sites",
  "reuters-dsewiki-openai-agent-breakout",
  "nvidia-hugging-face-definitive-agreement",
  "cisa-kev-artifactory-linux-kernel-openai-agent-flaws",
  "metr-redwood-eval-agent-coordination-investigation",
  "nvidia-hugging-face-reported-acquisition",
  "alabama-ag-openai-hugging-face-investigation-subpoena",
  "state-ags-openai-preservation-demand",
  "openai-exploitgym",
  "hf-llm-forensics"
 ],
 "Gated model access": [
  "anthropic-opus-5-5-cyber-request-routing",
  "google-fairwind-program",
  "google-gemini-3-8-flash-cyber",
  "openai-astra-critical-cyber",
  "anthropic-fable-mythos-5-1-access",
  "anthropic-mythos-5-defender-access-fund",
  "openai-daybreak-gpt56-cyber-gated-defenders",
  "openai-astra-critical-cyber-delay",
  "senate-ai-model-access-framework-letter"
 ],
 "Model-access abuse": [
  "carbonato-docker-botnet-hermes-agent",
  "team-cymru-llm-relay-transfer-stations",
  "anthropic-gtg50020-eval-sandbox-api-keys",
  "vulncheck-langflow-mass-exploitation",
  "anthropic-infostealer-claude-session-hijacking",
  "greynoise-fake-ai-crawler-credential-scanning",
  "metr-own-security-incidents",
  "unit42-ai-token-jacking",
  "okta-gray-market-frontier-model-access-proxies",
  "senate-ai-model-access-framework-letter"
 ],
 "Cyber insurance and AI liability": [
  "qbe-aig-boxx-affirm-ai-cyber-cover",
  "cfc-financial-institutions-affirmative-ai-cyber-wording",
  "beazley-ai-clarifying-endorsement-cyber-tech-eo",
  "aiuc-series-a-40m-frontier-insurance",
  "csis-insurance-ai-exclusions-retreat",
  "swiss-re-cyber-market-ai-era-2026",
  "reuters-carriers-ai-policy-language",
  "munich-re-at-bay-acquisition",
  "cowbell-ai-underwriting-factors",
  "ai-insurance-market-split-affirmative-vs-exclusions",
  "resilience-h1-2026-claims",
  "ibm-2026-cost-of-a-data-breach-ai-enabled",
  "naic-summer-2026-ai-agenda",
  "coalition-cyber-cover-method-neutral",
  "assured-cyber-agent-chaining",
  "am-best-stable-cyber-insurance-outlook",
  "aiuc-silent-ai-cover"
 ],
 "AI infrastructure as attack surface": [
  "hush-security-mcp-config-hardcoded-credentials",
  "irregular-agentic-self-modification-open-weights",
  "gitlab-duo-chat-credential-flaw-probes",
  "exposed-self-hosted-ai-endpoints-census",
  "sglang-safeunpickler-bypass-cve-2026-86793",
  "deepseek-harness-sandbox-escape-cve-2026-82533",
  "cisa-kev-litellm-mcp-auth-bypass",
  "pillar-grafana-mcp-session-spoofing-ssrf",
  "vulncheck-langflow-mass-exploitation",
  "metasploit-langflow-flowise-ai-platform-modules",
  "vulncheck-langflow-ai-stack-exploitation",
  "servicenow-ai-platform-critical-flaws",
  "wiz-ai-infrastructure-honeypot-attacks",
  "microsoft-ai-gateway-orchestration-intrusions",
  "rand-model-weight-security-sl3",
  "nemoclaw-ollama-dns-rebinding-model-poisoning",
  "mlflow-ssrf-cve-2026-64849-exploited",
  "cisa-kev-ray-ai-framework-cve-2025-62593-exploited",
  "cisa-kev-langflow-cve-2026-9198-exploited",
  "terraform-mcp-server-cross-tenant-credential-reuse-patch",
  "nist-sp-800-239-ai-datacenter",
  "orca-state-of-ai-security-unpatched-ai-packages"
 ],
 "Defeating the AI defender": [
  "checkpoint-puzzlemask-gatekeeper-bypass",
  "nightmare-eclipse-endpoint-zero-day-pocs",
  "eset-guardbreaker-llm-guardrail-malware",
  "unit42-perturbation-probing-safety-neurons",
  "arxiv-autobypass-endpoint-evasion",
  "arxiv-cot-monitor-collapse",
  "adversa-skill-scanner-bypass",
  "aisi-control-red-team-monitor-vulnerabilities",
  "dreadnode-scopejudge-offensive-agent-gating"
 ],
 "Frontier cyber thresholds crossed": [
  "anthropic-opus-5-5-cyber-request-routing",
  "von-der-leyen-soteu-ai-hacking-warning",
  "china-mss-chen-yixin-frontier-model-cyber-warning",
  "hacktron-claude-opus-5-openai-monorepo-access",
  "amodei-pace-the-frontier-botnet-warning",
  "openai-alien-mind-superhuman-intrusion",
  "openai-gpt6-astra-safety-overview-monitorability",
  "openai-astra-critical-cyber",
  "anthropic-mythos-5-1-system-card",
  "openai-preparedness-framework-rewrite-frontier-rl-hold",
  "gemini-3-7-flash-cyber-alert-threshold",
  "openai-astra-critical-cyber-delay",
  "crs-in-focus-executive-order-14409-explained",
  "meta-muse-spark-11-cyber-high-risk-not-ruled-out",
  "openai-gpt5-6-high-cybersecurity-capability-designation"
 ],
 "Vulnerability disclosure at machine speed": [
  "cisco-ise-auth-bypass-actively-exploited",
  "cisco-ise-hardening-frontier-ai-discovery",
  "microsoft-september-2026-patch-tuesday-record",
  "calif-weworm-wechat-zero-click",
  "echo-mythos-readiness-unreviewed-findings",
  "vulncheck-ai-poc-flood",
  "google-mandiant-avdh-agentic-vuln-discovery",
  "sharepoint-agent-found-flaw-exploited",
  "beazley-security-q2-vulnerability-surge",
  "rapid7-q2-2026-cve-doubling",
  "wiz-red-agent-snowflake-ci-injection",
  "metr-discovery-versus-exploitation-rates",
  "nist-nvd-modernization-ai-rfi",
  "rapid7-ai-assisted-sharepoint-rce-chain",
  "asecurity-zoomsday-ai-zoom-rce",
  "off-by-1-labs-ai-generated-patches-mostly-broken",
  "portswigger-http-terminator-ai-novel-desync",
  "unit42-nova-vulnerability-burst",
  "epoch-july-cve-severity-spike",
  "cve-program-frontier-ai-cna-pilot",
  "vulncheck-1h-2026-ai-vuln-exploitation-rate",
  "xbow-bing-images-autonomous-rce",
  "microsoft-patch-tuesday-record-ai-copilot-cves",
  "white-house-gold-eagle-ai-vulnerability-clearinghouse",
  "microsoft-ai-discovery-patch-volume"
 ],
 "Distillation as exfiltration": [
  "team-cymru-llm-relay-transfer-stations",
  "peoples-daily-rejects-us-distillation-claims",
  "anthropic-seven-china-labs-distillation",
  "nsa-cisa-fbi-china-ai-distillation-advisory",
  "blade-act-model-extraction"
 ],
 "US signals agencies reorganising around AI": [
  "nsa-five-mission-centers-ai-cyber",
  "cybercom-chief-ai-officer-green"
 ],
 "The pacing debate and the political answer": [
  "bessent-us-china-ai-incident-notification-mechanism",
  "openai-confirms-multilab-safety-coordination",
  "treasury-ftc-reject-ai-lab-carve-outs",
  "trump-rejects-ai-slowdown-guardrails",
  "amodei-pace-the-frontier-botnet-warning",
  "ban-artificial-superintelligence-act",
  "openai-preparedness-framework-rewrite-frontier-rl-hold",
  "sanders-ai-development-pause-letter",
  "oncd-cairncross-black-hat-open-source-ai-and-no-regulatory-regime"
 ]
}

ORDER = ["evaluation-incidents", "frontier-capability", "ai-in-attacks", "attacks-on-ai",
         "ai-found-vulnerabilities", "critical-infrastructure"]

p = Path(__file__).resolve().parent.parent / "data.json"
raw = p.read_text(encoding="utf-8")
d = json.loads(raw)
n = 0
for it in d["items"]:
    it.pop("threads", None)
    tags = TOPICS.get(it["id"], [])
    if tags:
        merged = sorted(set(it.get("topics", [])) | set(tags), key=ORDER.index)
        if merged != it.get("topics"):
            it["topics"] = merged
            n += 1
for w in d.get("watchlist", []):
    if w.get("thread") in WATCH_TOPICS and not w.get("topic"):
        w["topic"] = WATCH_TOPICS[w["thread"]]
    if w.get("thread") in WATCH_ITEMS:
        have_ids = {i["id"] for i in d["items"]}
        merged = list(dict.fromkeys(w.get("items", []) + [i for i in WATCH_ITEMS[w["thread"]] if i in have_ids]))
        w["items"] = merged
have = {(c["date"], c.get("item")) for c in d.get("corrections", [])}
new = [c for c in CORRECTIONS if (c["date"], c.get("item")) not in have]
d["corrections"] = d.get("corrections", []) + new
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + ("\n" if raw.endswith("\n") else ""),
             encoding="utf-8")
print(f"tagged {n} items, added {len(new)} corrections")
