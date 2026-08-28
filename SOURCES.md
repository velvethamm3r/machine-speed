# Machine Speed — source scan list

The canonical list of places a run sweeps. It is a research checklist, **not** a file
the build reads: `build.py` only ever renders `data.json`. This list sits alongside
`RUNBOOK.md`, `SCHEMA.md` and `dashboard-memory.md` and is pointed to from
`DAILY_RUN.md` step 3.

## How to use it

- Each run works this list for anything published since the last `coverageEnd`, plus
  anything **new to the board** that still falls inside the window.
- It is the **floor, not the ceiling.** Follow any lead a source hands you past the edge
  of the list; then, if the new source is worth keeping, add it here.
- **Primary source first.** Cite the party that produced the finding — the lab's own post,
  the agency's own advisory, the vendor's own research blog — not an outlet reporting on it,
  whenever the primary can be opened. Every item still has to be a page you actually opened
  and read. Press is a fallback, noted as such.
- **Most of these do not move on a given day, and that is fine.** An empty lane is an honest
  outcome. Never pad a lane to fill the list.
- The tags in brackets are the lanes a source most often feeds: `cap` capability · `pol`
  policy · `def` defense · `atk` attacks · `mkt` markets. They are a hint, not a rule — a
  lab can produce a `pol` item and an agency a `cap` one.
- Some vendor and lab blogs sit behind bot-checks or need a fetch approval that an unattended
  run cannot give; when the primary can't be opened, carry the item on press with a "(via …)"
  attribution and upgrade it on a later attended run (this is the standing practice in
  `dashboard-memory.md`). **A blocked primary is not an empty one:** before treating that source's
  lane as quiet, run a site-scoped search for its last ~48 hours of posts (e.g. `site:openai.com`
  plus the date window and a cyber keyword) and open whatever it surfaces — a broad topical query
  buries the day's actual post under aggregators and older look-alikes. See `DAILY_RUN.md` →
  "Sourcing" for the full rule and the 2026-08-28 cautionary case.

_Entry points below were confirmed reachable on 2026-08-24. Keep them current: retire a dead
source by replacing or removing its line rather than leaving a link that 404s._

---

## 1. Frontier AI labs — `cap` `def`

The labs disclose their own models' cyber behaviour, ship cyber-tuned models, and publish
capability and safety findings. Their own posts are `on-record` for disclosures and
`self-reported` for benchmark/capability claims.

- **OpenAI** — News index https://openai.com/news/ · individual posts under https://openai.com/index/ · watch Preparedness / safety and security posts. `cap` `def`
- **Anthropic** — News https://www.anthropic.com/news · security, Mythos/Frontier Red Team, disclosures. `cap` `def` `atk`
- **xAI (Grok)** — News https://x.ai/news. `cap` `def`
- **Google DeepMind** — Blog https://deepmind.google/discover/blog/ · CodeMender, Big Sleep, frontier safety. `cap` `def`
- **Meta AI** — Blog https://ai.meta.com/blog/ (also open-weight, §4). `cap`

## 2. Big-tech platforms & their threat-intel arms — `def` `atk` `cap`

- **Google Security Blog** — https://security.googleblog.com/. `def` `atk`
- **Google Threat Intelligence Group / Mandiant** — https://cloud.google.com/blog/topics/threat-intelligence/ · Mandiant https://www.mandiant.com/resources/blog · GTIG AI Threat Tracker, AVDH. `atk` `cap` `def`
- **Google Project Zero** — https://googleprojectzero.blogspot.com/. `cap` `def`
- **Microsoft Security Blog** (incl. MSTIC threat intelligence) — https://www.microsoft.com/en-us/security/blog/. `def` `atk`
- **Microsoft MSRC** — Blog https://msrc.microsoft.com/blog/ · Update Guide / Patch Tuesday https://msrc.microsoft.com/update-guide/. `def`

## 3. Cyber & threat-intel vendors — `atk` `def` `cap`

**Named core**

- **CrowdStrike** — https://www.crowdstrike.com/blog/ (Counter Adversary Operations, Threat Hunting Report). `atk` `def`
- **Palo Alto Networks — Unit 42** — https://unit42.paloaltonetworks.com/. `atk` `def`

**Regularly cited on the board**

- **Rapid7** — https://www.rapid7.com/blog/. `atk` `cap`
- **Trellix Advanced Research Center** — https://www.trellix.com/blogs/research/. `atk`
- **Varonis Threat Labs** — https://www.varonis.com/blog. `def` `atk`
- **Sysdig** — https://www.sysdig.com/blog. `atk`
- **Zscaler ThreatLabz** — https://www.zscaler.com/blogs/security-research. `atk`
- **Cisco Talos** — https://blog.talosintelligence.com/. `atk` `def`
- **Check Point Research** — https://research.checkpoint.com/. `atk`
- **SentinelOne Labs** — https://www.sentinelone.com/labs/. `atk` `def`
- **Wiz** — https://www.wiz.io/blog. `def`
- **watchTowr Labs** — https://labs.watchtowr.com/. `atk`
- **Okta Threat Intelligence** — https://sec.okta.com/. `atk`
- **Hunt.io** — https://hunt.io/blog. `atk`

**AI-security specialists**

- **Adversa AI** — https://adversa.ai/blog/. `def` `cap`
- **Pillar Security** — https://www.pillar.security/blog. `def`
- **HiddenLayer** — https://hiddenlayer.com/research/. `def`
- **Protect AI** — https://protectai.com/blog. `def`
- **XBOW** — https://xbow.com/blog (offensive-capability comparisons). `cap`
- **PromptArmor** — research posts (often co-disclosed via The Hacker News). `def`

## 4. Open-source / open-weight AI — `cap` `def`

The open-weight developers and the "open-weight cyber gap" storyline: model releases,
benchmark claims, and hold-backs for cyber-safety review.

- **Hugging Face** — Blog https://huggingface.co/blog · Papers https://huggingface.co/papers · security/incident disclosures. `cap` `def` `atk`
- **Meta (Llama / Muse)** — https://ai.meta.com/blog/ · https://www.llama.com/. `cap`
- **Z.ai (GLM)** — https://z.ai/blog. `cap`
- **Moonshot AI (Kimi)** — https://platform.moonshot.ai/blog. `cap`
- **DeepSeek** — https://www.deepseek.com/ (news/updates). `cap`
- **Mistral AI** — https://mistral.ai/news/. `cap`
- **Alibaba Qwen** — https://qwenlm.github.io/blog/. `cap`
- **Open Secure AI Alliance (OSAIA) / Linux Foundation** — https://linuxfoundation.org/ (agentic-AI incident sharing, sandbox runtimes). `def`
- **OWASP GenAI Security Project** — https://genai.owasp.org/ (LLM Top 10). `def`

Open-weight cyber-capability numbers (CyberGym, ExploitBench, XBOW head-to-heads) usually
surface through the labs above and the vendors in §3 — capture them `self-reported` until
independently reproduced.

## 5. Academic, research & evaluation institutions — `cap` `pol` `def`

Groups that evaluate and report on AI/cyber independently of the labs.

**Eval & AI-safety labs**

- **UK AI Safety Institute (AISI)** — https://www.aisi.gov.uk/ (also §7). `cap` `def`
- **METR** — https://metr.org/. `cap`
- **Apollo Research** — https://www.apolloresearch.ai/. `cap`
- **Epoch AI** — https://epoch.ai/. `cap`
- **MITRE** — ATLAS (adversarial ML) https://atlas.mitre.org/ · ATT&CK https://attack.mitre.org/. `def`

**University centers**

- **arXiv** — cs.CR https://arxiv.org/list/cs.CR/recent · cs.AI https://arxiv.org/list/cs.AI/recent · mirror https://www.alphaxiv.org/. `cap` `def`
- **Georgetown CSET** — https://cset.georgetown.edu/. `pol` `cap`
- **Stanford HAI / CRFM / Internet Observatory** — https://hai.stanford.edu/. `cap` `pol`
- **UC Berkeley — Center for Long-Term Cybersecurity (CLTC)** — https://cltc.berkeley.edu/. `pol` `def`
- **Carnegie Mellon — SEI / CERT & CyLab** — https://insights.sei.cmu.edu/ · https://www.cylab.cmu.edu/. `def`
- **Oxford — Centre for the Governance of AI (GovAI)** — https://www.governance.ai/. `pol`
- **SANS Internet Storm Center** — https://isc.sans.edu/. `def` `atk`

**Think tanks & trackers**

- **RAND** — https://www.rand.org/ (AI, cyber, human-uplift studies). `pol` `cap`
- **CSIS** — https://www.csis.org/ · Significant Cyber Incidents tracker. `pol` `atk`
- **Center for a New American Security (CNAS)** — https://www.cnas.org/. `pol`
- **Atlantic Council — Cyber Statecraft Initiative / DFRLab** — https://www.atlanticcouncil.org/. `pol`
- **Brookings** — https://www.brookings.edu/. `pol`

## 6. US government & agencies — `pol` `def` `atk`

- **CISA** — Cybersecurity Advisories https://www.cisa.gov/news-events/cybersecurity-advisories · Known Exploited Vulnerabilities (KEV) https://www.cisa.gov/known-exploited-vulnerabilities-catalog · News https://www.cisa.gov/news-events/news. `pol` `def` `atk`
  - _Note: cisa.gov blocks automated fetchers (HTTP 403), so an unattended run usually cannot open a CISA page directly. To source a KEV entry, open the CVE on **NVD** (§10) — the NVD record carries the CISA KEV "Date Added" and "Due Date," so it confirms the KEV determination on a government primary. IC3 advisory PDFs (ic3.gov) and the co-sealed agency pages are often reachable when cisa.gov is not._
- **NSA** — Cybersecurity Advisories & Guidance https://www.nsa.gov/Cybersecurity/Cybersecurity-Advisories-Guidance/. `def` `atk`
- **FBI IC3** — https://www.ic3.gov/ · Industry alerts / PSAs https://www.ic3.gov/Home/IndustryAlerts. `atk`
- **NIST** — AI https://www.nist.gov/artificial-intelligence · CAISI (Center for AI Standards & Innovation) https://www.nist.gov/caisi · CSRC news https://csrc.nist.gov/news. `pol` `def`
- **White House** — Presidential actions https://www.whitehouse.gov/presidential-actions/ · Executive orders https://www.whitehouse.gov/presidential-actions/executive-orders/ (memoranda, EOs; OSTP / ONCD releases appear here too). `pol`

## 7. Congress & policy — `pol`

- **Congress.gov** — Legislation https://www.congress.gov/legislation · Advanced search https://www.congress.gov/advanced-search/legislation (filter on AI + cybersecurity; capture bill number, sponsors, status). `pol`
- **CRS Reports** — https://crsreports.congress.gov/ (In Focus explainers). `pol`
- **Member offices** — when a specific bill or letter is the event, cite the sponsor's own `.senate.gov` / `.house.gov` press release or letter PDF. `pol`

## 8. State & local government — `pol` `atk` `def`

State-level AI and cyber moves are in remit and already on the board (Illinois SB 315, California's
Newsom AI Cyber Defense Program, New York's water rules, the multistate AG demand to OpenAI). Watch
state legislation, governor and AG actions, and state/local incidents — cite the state's own primary
(the governor's office, the bill page, the AG newsroom) whenever a specific action is the event.

- **NCSL** — Artificial-intelligence legislation https://www.ncsl.org/technology-and-communication/artificial-intelligence-2026-legislation · Cybersecurity legislation https://www.ncsl.org/technology-and-communication/cybersecurity-legislation. `pol`
- **MultiState — AI legislation tracker (all 50 states)** — https://www.multistate.ai/artificial-intelligence-ai-legislation. `pol`
- **IAPP — US State AI Governance Legislation Tracker** — https://iapp.org/resources/article/us-state-ai-governance-legislation-tracker/. `pol`
- **State governors & legislatures** — cite the primary when a specific law or program is the event: e.g. California https://www.gov.ca.gov/ · New York https://www.governor.ny.gov/ · Illinois General Assembly https://www.ilga.gov/. `pol` `def`
- **State attorneys general** — coalition actions and enforcement; individual AG newsrooms (e.g. Iowa https://www.iowaattorneygeneral.gov/newsroom · California https://oag.ca.gov/news · New York https://ag.ny.gov/press-releases · Texas https://www.texasattorneygeneral.gov/news) and NAAG https://www.naag.org/. `pol`
- **StateScoop** — state & local government technology and cyber news. https://statescoop.com/. `pol` `atk` `def`
- **MS-ISAC / Center for Internet Security** — state, local, tribal & territorial incident coordination. https://www.cisecurity.org/ms-isac. `atk` `def`
- **State cyber agencies & fusion centers** — when named in an event (e.g. California Cybersecurity Integration Center / Cal-CSIC). `def` `atk`

## 9. Joint & international advisory channels — `atk` `def` `pol`

Joint advisories arrive through the agency feeds in §6 (a CISA `AAxx-xxxA` advisory co-sealed
with NSA / FBI / DC3 / EPA / DOE and international partners). Watch these directly too:

- **UK NCSC** — https://www.ncsc.gov.uk/. `def` `pol`
- **EU — European Commission (Digital)** — https://digital-strategy.ec.europa.eu/ · **ENISA** https://www.enisa.europa.eu/. `pol` `def`
- **Five Eyes partners** — Australia ASD/ACSC https://www.cyber.gov.au/ · Canada CCCS https://www.cyber.gc.ca/ · New Zealand NCSC https://www.ncsc.govt.nz/ (usually co-signed on the joint advisories). `atk` `def`

## 10. Vulnerability & CVE registries — verification (cross-lane)

Used to verify — never invent — a CVE, its CVSS or its status before it goes on the board.

- **CVE.org** — https://www.cve.org/ (is the CVE actually assigned?). 
- **NVD** — https://nvd.nist.gov/ (CVSS, status).
- **GitHub Advisory Database** — https://github.com/advisories (GHSA records).
- **VulnCheck** — https://vulncheck.com/blog (exploitation-in-the-wild data).

## 11. Markets / cyber-insurance — `mkt`

- **Insurance Business** — https://www.insurancebusinessmag.com/us/cyber/. `mkt`
- **AM Best** — https://news.ambest.com/. `mkt`
- **Carrier / broker / reinsurer primaries** when cited (Munich Re, Swiss Re, Lloyd's, CFC, Coalition, Chaucer/Armilla, AIG, Berkley) — use the primary; carrier/broker marketing is `self-reported` unless a regulator, court or loss report says otherwise. `mkt`
- **Research reports** — IBM Cost of a Data Breach, ISO filings/endorsements. `mkt`

---

## Extending this list

Add a source under the heading that fits it, with its **primary** URL and a lane tag or two.
Keep the primary-source-first rule: prefer a research blog, an agency page or a lab post over
an aggregator. When a source stops publishing or moves, replace or remove its line in the same
edit rather than leaving a dead link. This file is documentation only — changing it never
touches the build or the layout.
