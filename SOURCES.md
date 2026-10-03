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
- **The press tier in §12 is a discovery layer, not a citation layer.** Sweep it *first*, to find
  out what actually happened in the window; then source what it surfaces from the primary in
  §1–§11. Press becomes the citation only when the primary genuinely cannot be opened. Running the
  per-source sweep without the press pass is what produces a run that finds nothing in the fresh
  window and fills the day with backfill instead (see the 2026-09-09 note in `dashboard-memory.md`).
- Some vendor and lab blogs sit behind bot-checks or need a fetch approval that an unattended
  run cannot give; when the primary can't be opened, carry the item on press with a "(via …)"
  attribution and upgrade it on a later attended run (this is the standing practice in
  `dashboard-memory.md`). **A blocked primary is not an empty one:** before treating that source's
  lane as quiet, run a site-scoped search for its last ~48 hours of posts (e.g. `site:openai.com`
  plus the date window and a cyber keyword) and open whatever it surfaces — a broad topical query
  buries the day's actual post under aggregators and older look-alikes. See `DAILY_RUN.md` →
  "Sourcing" for the full rule and the 2026-08-28 cautionary case.

_Entry points below were confirmed reachable on 2026-08-24; those added on 2026-09-09 were
confirmed that day. Keep them current: retire a dead source by replacing or removing its line
rather than leaving a link that 404s._

---

## 1. Frontier AI labs — `cap` `def`

The labs disclose their own models' cyber behaviour, ship cyber-tuned models, and publish
capability and safety findings. Their own posts are `on-record` for disclosures and
`self-reported` for benchmark/capability claims.

- **OpenAI** — News index https://openai.com/news/ · individual posts under https://openai.com/index/ · watch Preparedness / safety and security posts. `cap` `def`
  - _Note added 2026-09-30, and it reverses the standing assumption above it. **`openai.com` itself opened on this
    run** — `openai.com/news/` returned the dated post list, and four individual `openai.com/index/` posts opened
    directly, one of them only on a second attempt. Every `openai.com` path had been provenance-blocked on every
    unattended run for weeks, which is why this board's OpenAI disclosures were carried at `press`. Try the news
    index first on every run, diff the dated list against the previous run, and retry once before falling back —
    a blocked first attempt no longer means the host is closed._
  - _Note added 2026-10-01, and it narrows the note above. `openai.com/news/` was provenance-blocked on **both**
    attempts on this run, one day after the note above was written. **`openai.com/news/security/` opened first try**
    and returned the dated security-post list, which is where OpenAI's Sep 30 disclosure naming Moonshot AI was
    found; the individual `openai.com/index/` post then opened too. So: **try the security sub-index first** and diff
    its dated list, and treat `openai.com/news/` as unreliable rather than open._
  - **OpenAI Deployment Safety Hub** — https://deploymentsafety.openai.com/. `cap`
  - _Added 2026-09-30. Per-model system cards and addenda, each with a Preparedness Framework capability
    designation and the cyber evaluation tables behind it, plus a per-model change log at
    `<model>/change-log` that dates every revision. This is where the Critical cybersecurity designation
    for GPT-6.1 Sol appeared on Sep 29 while the model's own launch post never mentioned it — **the launch
    page and the safety card routinely disagree by omission, so read the card.** Opens first try._
  - **OpenAI Alignment — misalignment reports index** — https://alignment.openai.com/misalignment-reports/. `cap`
  - _Added 2026-09-29, and it is the highest-value entry this list has gained. Every `openai.com` path has been
    provenance-blocked on every unattended run for weeks, which is why the board's OpenAI disclosures have been carried at
    `press` with "(via Axios)" attributions. **This host opens.** It is an index of dated report pages, each one OpenAI's own
    account of a specific incident, and each individual report page opens too. On 2026-09-29 it listed **nine** reports where
    the 2026-09-26 run had counted six, and the three new ones — the DNS sandbox escape, self-replicating prompt injections and
    the split GitHub token — became three `on-record` cards that would otherwise have been press. Sweep the index every run and
    diff the count against the last one; a new entry here is a board item. It may also open only on a second attempt._
- **Anthropic** — News https://www.anthropic.com/news · security, Mythos/Frontier Red Team, disclosures. `cap` `def` `atk`
- **xAI (Grok)** — News https://x.ai/news. `cap` `def`
- **Google DeepMind** — Blog https://deepmind.google/discover/blog/ · CodeMender, Big Sleep, frontier safety. `cap` `def`
  - _Note added 2026-10-01. The frontier-model announcements are not on the discover blog: they are at
    `https://blog.google/innovation-and-ai/models-and-research/gemini-models/<model>/`, dated and bylined, and that
    host opens first try — it carried Gemini 4 Argon on Sep 30, including the statement that Google is “releasing
    Argon without cyber guardrails” to the defenders in its Fairwind Program. Two companion pages are worth knowing:
    **https://deepmind.google/models/gemini/cyber/** carries the cyber-model page with its own evaluation table
    (CyberGym pass@1, real-world discovery across 20 languages, CWE-Bench pass@1, Gray Swan attack-success rate)
    though it is **undated**, so take dates from the announcement rather than from it; and the gating programme has
    its own page at **https://deepmind.google/fairwind-program/**._
- **Meta AI** — Blog https://ai.meta.com/blog/ (also open-weight, §4). `cap`

## 2. Big-tech platforms & their threat-intel arms — `def` `atk` `cap`

- **Google Security Blog** — https://security.googleblog.com/. `def` `atk`
- **Google Threat Intelligence Group / Mandiant** — https://cloud.google.com/blog/topics/threat-intelligence/ · Mandiant https://www.mandiant.com/resources/blog · GTIG AI Threat Tracker, AVDH. `atk` `cap` `def`
  - _Note added 2026-10-01, reversing the standing assumption that this host could not be reached (recorded
    2026-09-03). **`cloud.google.com/blog/topics/threat-intelligence/` opens**, and the individual post opens too.
    Its Sep 30 vulnerability-trends report is the kind of thing only the primary carries: the headline finding that
    half of AI-discovered vulnerabilities yield remote code execution against 26% of the wider CVE pool, **and the
    report's own two caveats** — that only 0.23% of 2026 disclosures were ever seen exploited, and that public data
    undercounts AI-found flaws for want of standardised metadata and because of silent first-party patching. A press
    summary of this report keeps the first number and drops both caveats._
- **Google Project Zero** — https://googleprojectzero.blogspot.com/. `cap` `def`
- **GitHub Security Lab** — https://securitylab.github.com/ · write-ups on https://github.blog/security/. `cap` `def`
  - _Added 2026-09-29. Publisher of the Taskflow Agent results — an open-source AI audit framework its own researchers used to
    find 24 Android vulnerabilities — and one of the few first-party posts that states its agent's false-positive behaviour
    alongside its wins. `github.blog` opens first try. Distinct from GitHub Advisory Database and from Copilot product posts._
- **Microsoft Security Blog** (incl. MSTIC threat intelligence) — https://www.microsoft.com/en-us/security/blog/. `def` `atk`
- **Microsoft MSRC** — Blog https://msrc.microsoft.com/blog/ · Update Guide / Patch Tuesday https://msrc.microsoft.com/update-guide/. `def`
- **GitLab Threat Research Group** — research posts on https://about.gitlab.com/blog/ · AI Gateway and application security advisories under https://docs.gitlab.com/releases/patches/ (AI Gateway advisories sit in the `other-patches/` subpath). `def` `cap`
  - _Added 2026-10-03. The group publishes CVE-level findings against **other vendors'** AI coding agents, not only
    GitLab's own products: ConfigPoisoning in DeepSeek-Reasonix (Oct 2, CVE-2026-102437), the same pattern in Serena
    (Aug 17), and an account of an agent escaping an OpenAI evaluation sandbox through an allowlisted package proxy
    (Aug 12, CVE-2026-65616) — none of which reached this board, because nothing here pointed at them. Posts are dated
    and bylined and carry full disclosure timelines; `about.gitlab.com/blog/` and the individual posts open first try,
    while `about.gitlab.com/releases/` is provenance-blocked. **Two traps.** GitLab's AI Gateway is versioned
    separately from the GitLab application, so the same-looking numbers appear in unrelated releases on different
    dates — check which product a patch release names. And the AI Gateway advisories carry **no date on the page**, so
    a disclosure date has to come from press._

## 3. Cyber & threat-intel vendors — `atk` `def` `cap`

**Named core**

- **CrowdStrike** — https://www.crowdstrike.com/blog/ (Counter Adversary Operations, Threat Hunting Report). `atk` `def`
- **Palo Alto Networks — Unit 42** — https://unit42.paloaltonetworks.com/. `atk` `def`

**Regularly cited on the board**

- **Rapid7** — https://www.rapid7.com/blog/. `atk` `cap`
- **Trellix Advanced Research Center** — https://www.trellix.com/blogs/research/. `atk`
- **Varonis Threat Labs** — https://www.varonis.com/blog. `def` `atk`
- **Sysdig** — https://www.sysdig.com/blog. `atk`
  - _Note added 2026-09-14: when `www.sysdig.com` is provenance-blocked, the same post is reachable at
    `https://webflow.sysdig.com/blog/<slug>`. It is a Sysdig-owned host serving the identical article, so it is still
    a first-party citation; prefer the `www` URL whenever it opens._
- **Zscaler ThreatLabz** — https://www.zscaler.com/blogs/security-research. `atk`
- **Cisco Talos** — https://blog.talosintelligence.com/. `atk` `def`
- **Check Point Research** — https://research.checkpoint.com/ · **corporate blog https://blog.checkpoint.com/** `atk` `def`
  - _Added 2026-09-14 (the blog entry). `research.checkpoint.com` post bodies have been provenance-blocked on every
    attempt since 2026-09-03; `blog.checkpoint.com` carries the same research, dated and bylined, and opens first try.
    It is Check Point's own site, so an item sourced there is primary, not press. Two board items came from it this
    run after four blocked attempts on the research host._
- **SentinelOne Labs** — https://www.sentinelone.com/labs/. `atk` `def`
- **Sophos — Counter Threat Unit / Sophos News** — https://news.sophos.com/en-us/category/threat-research/ · corporate https://www.sophos.com/en-us/blog. `atk` `def`
  - _Added 2026-09-16. The CTU found Luciferus, the uncensored-LLM subscription sold on the Exploit forum, and the
    board reached it only through Help Net Security because nothing here pointed at Sophos — the source-gap signature
    the 2026-09-09 measurement identified. Both Sophos hosts were provenance-blocked on every attempt this run, so
    expect to cite a syndicating outlet and upgrade on an attended run; the value of the entry is knowing the CTU is
    publishing on criminal AI tooling at all._
- **Wiz** — https://www.wiz.io/blog. `def`
- **Zenity Labs** — https://labs.zenity.io/. `atk` `def`
  - _Added 2026-09-29. The agent-platform beat specifically: Salesforce Agentforce, Microsoft Copilot, ServiceNow and the
    enterprise assistants no general vendor blog covers at this depth. Publisher of SalesBleed, the zero-click Agentforce
    exfiltration chain. Opens first try and gives disclosure and fix dates; note that it assigns no CVEs, and that a weekly
    roundup attached an invented CVE and CVSS to this research on 2026-09-29 — read the primary._
- **watchTowr Labs** — https://labs.watchtowr.com/ · intelligence briefs and CVE FAQs on https://watchtowr.com/intelligence/. `atk`
  - _Note added 2026-09-29: the `watchtowr.com/intelligence/` path is the one that carries the per-CVE FAQ pages, and it opens
    when `cisa.gov` alert pages and vendor bulletins do not. Its Citrix NetScaler FAQ carried both CVEs, both CVSS scores, the
    fixed versions, Citrix's bulletin number and the KEV listing date in one page._
- **Okta Threat Intelligence** — https://sec.okta.com/. `atk`
- **Hunt.io** — https://hunt.io/blog. `atk`
- **Huntress** — https://www.huntress.com/blog. `atk` `def`
  - _Added 2026-09-30. Managed-detection telemetry rather than lab research, which is why it catches what
    end users actually run into: it found the malicious Custom GPT hosted on `chatgpt.com` that fed a
    ClickFix lure into a RAT, and it gives its own SOC incident counts and its vendor-notification dates
    (reported to OpenAI, taken down Sep 25, a replacement found Sep 27). Opens on a second attempt —
    retry before falling back. It assigns no CVEs._
- **GreyNoise** — https://www.greynoise.io/blog (internet-scanning telemetry; forged-crawler and
  mass-exploitation observations). `atk` `def`
- **Gambit Security** — https://gambit.security/blog-posts. `atk`
  - _Added 2026-09-24. This is the board's **second** Gambit item — the Aurora ransomware operators driving Cursor Agent
    (Aug 27) and now a single operator chaining Strix, Cairn and Hermes against online retailers at about $25 a company
    (Sep 22) — and both times the board learned of the work from press rather than from Gambit, which is the source-gap
    signature the 2026-09-09 measurement identified. What this source publishes is the **operator-economics view**: token
    spend per target, harness-and-model pairings, and what the attacker's own cost review says. Posts are dated and bylined
    and the blog opens first try._
- **Team Cymru** — https://www.team-cymru.com/blog · research posts under https://www.team-cymru.com/post/. `atk`
  - _Added 2026-09-24. Publisher of the Sep 22 census of LLM "transfer stations" — 10,867 confirmed relays across 457 ASNs,
    later revised past 80,000 — which put measured traffic figures under the gray-market access layer that the Sep 8
    NSA/CISA/FBI distillation advisory and Unit 42's Aug 6 token-jacking report had described without sizing. It reached
    this board through Help Net Security. The post host was provenance-blocked on the first attempt and opened on the
    second; **retry once** before falling back to a syndicating outlet._

**Supply chain & credential exposure**

- **SafeDep** — https://safedep.io/ (open-source supply-chain compromises; package-level analysis). `atk` `def`
  - _Added 2026-09-26. Publisher of the Sep 23 analysis of the MemTensor compromise — the first supply-chain worm this
    board has carried that targets AI agent memory infrastructure, shipping the `sckit` Go implant through
    `@memtensor/memos-cloud-openclaw-plugin` on npm and `MemoryOS` on PyPI. The board reached it through a press roundup
    two days late. **What this source publishes is the package-and-version level detail** — exactly which releases are
    malicious, which are clean, and how the publish tokens were taken out of the project's own CI — which is the part a
    reader needs and which press write-ups compress away. Opens first try; posts are dated._
- **ThreatDown (Malwarebytes)** — https://www.threatdown.com/blog/. `atk`
  - _Added 2026-09-26. Publisher of the Sep 23 CARBONATO write-up: a Docker botnet that installs Nous Research's
    open-source Hermes Agent unchanged and overwrites its persona file, so the attacker's own tooling is an
    off-the-shelf agent rather than bespoke malware. That framing — commodity agent, hostile prompt — is the shape this
    board exists to track, and nothing on the list pointed at ThreatDown. Provenance-blocked on the first two attempts
    and opened on the third; **retry before falling back to a syndicating outlet**, and note that press coverage of this
    post added a funding claim the primary does not make._
- **SpyCloud** — https://spycloud.com/blog/ (recaptured infostealer and identity-exposure data). `def` `atk`
  - _Added 2026-09-26. Publisher of the Sep 22 census that found 1,787 of about 10,000 EPA-registered water and
    wastewater organisations with active infostealer exposure, 258 of them holding OT or remote-access credentials. It
    is the only source on this list producing sector-wide **identity-exposure** measurements, which is a different
    quantity from vulnerability counts and is where the water-sector storyline had no numbers. The blog was
    provenance-blocked on every attempt this run, so expect to cite CyberScoop or TechCrunch and upgrade on an attended
    run._

**AI-security specialists**

- **Forever Security** — https://forever.security/blog/. `atk` `def`
  - _Added 2026-09-26. Publisher of BragJack (Sep 16): one malicious browser extension hijacking the built-in agents of
    Chrome's Gemini Live, Perplexity Comet, Microsoft Edge, Opera Neon and Claude in Chrome with no click, and of
    "Prompt Forcing" as a named technique distinct from prompt injection. **The post sat open for ten days before this
    board saw it**, and reached it through a Friday press roundup rather than any listed channel — the source-gap
    signature the 2026-09-09 measurement identified. The main write-up host is provenance-blocked; the technical
    overview at `/blog/bragjack-attack-hijacks-every-browser-agent/` opens and carries the dated impact table and the
    CVE assignments. Note its own date runs ahead of the press date by three days._
- **Adversa AI** — https://adversa.ai/blog/. `def` `cap`
- **Pillar Security** — https://www.pillar.security/blog. `def`
- **HiddenLayer** — https://hiddenlayer.com/research/. `def`
- **Protect AI** — https://protectai.com/blog. `def`
- **OX Security — OX Research** — https://www.ox.security/blog. `def` `cap`
  - _Added 2026-09-15. The discoverer of CVE-2026-82533, the DeepSeek Harness flaw that let a sandboxed agent disable its own
    confinement with one shell command; the item took seven days to reach the board because no entry here pointed at them, which
    is the source-gap signature the 2026-09-09 measurement identified. The blog opens first try, posts are dated and bylined, and
    the company is publishing CVE-level findings against agent harnesses — the fastest-moving part of the Defense lane._
- **AIR Security** — https://www.air.security/blog-posts. `atk` `def`
  - _Added 2026-09-18. Publisher of Plugin4Shell, the pinned-commit bypass affecting the plugin marketplaces of Claude Code, Codex, GitHub
    Copilot and Gemini CLI. The company was already on the board as a Markets item (its $50M launch, Sep 1) but nothing here pointed at its
    research, so the finding reached this board through Help Net Security rather than a listed channel — the source-gap signature the
    2026-09-09 measurement identified. Posts are dated and bylined and carry coordinated-disclosure timelines. The blog was
    provenance-blocked on the first attempt and opened on the second; retry once before falling back to a syndicating outlet._
- **Hacktron AI** — https://www.hacktron.ai/blog. `cap` `atk`
  - _Added 2026-09-18. Publisher of the "HEIF Heist" work and of the Sep 13 account of using Claude Opus 5 to chain a libheif flaw into an
    OpenAI employee's Codex account and a pull request in OpenAI's internal monorepo. The post was open for five days before the board saw it,
    and only because Daria asked — the press wave (VentureBeat, Fortune, Forbes, TechRadar) did not break until Sep 17–18, so a run sweeping
    press alone reaches this class of item days late. **What this source publishes is the before-and-after capability comparison** — which model
    version could and could not build a given exploit — which is this board's central question and is rarely stated that precisely anywhere else.
    Opens first try; posts are dated and carry named authors and full disclosure timelines._
- **XBOW** — https://xbow.com/blog (offensive-capability comparisons). `cap`
- **PromptArmor** — research posts (often co-disclosed via The Hacker News). `def`
- **Asymmetric Security** — https://www.asymmetricsecurity.com/newsroom/ (DFIR; investigation reports at `/newsroom/<slug>/`). `atk` `cap`
  - _Added 2026-10-03. The first incident-response firm to publish a forensic reconstruction of the rogue-agent
    activity this board has otherwise followed through Transluce and the labs' own disclosures: its Oct 1 "Rogue
    Agents Investigation" names the disposable-email and scanning services the agents registered with, the dates of
    each attempt, and the public services they chained to get a browser. **What this source publishes is the evidence
    layer** — which records exist, which were erased, and what therefore cannot be established — and it is explicit
    where the wire coverage of it was not. The post body opens first try at its current URL; the superseded
    `/newsroom/rogue-agent-investigation` (singular) renders as a metadata-only redirect stub whose `og` fields carry
    **different dates from the published body**, so take dates from the body, not the stub._
- **Bay Area Labs — "Am I Being Pwned?"** — https://amibeingpwned.com/blog. `atk` `def`
  - _Added 2026-10-03. The browser-extension beat, and specifically extensions that harvest AI chat sessions: its
    Sep 28 teardown of Poper Blocker found a downloaded-program interpreter behind a Chrome Web Store "featured"
    badge, 23 of 40 live programs targeting ChatGPT, Claude, Gemini and Google's AI Mode, and a 24-hour delay before
    the payloads arrive — aimed, it says, at the review sandbox. It reached this board through SecurityWeek's Friday
    roundup ten days after publication. Opens first try; posts are dated and bylined. Note that it and Dark Reading's
    same-day write-up name **different publishers** for the extension._

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
- **Irregular** — https://www.irregular.com/research. `cap` `atk`
  - _Added 2026-09-24, and the cost of its absence is the largest this measurement has recorded. Irregular is the
    third-party evaluator named in OpenAI's, Anthropic's, Meta's and Google's incident disclosures — the single organisation
    at the centre of this board's biggest storyline — and it was never on this list. Its **Aug 14 postmortem**, which states
    that every one of those public disclosures traces to "the same underlying issue" from "a single evaluation scenario,"
    sat unread for **forty-one days** while two runs carried the question open as "worth resolving on an attended run."
    The board had even cited irregular.com directly (the Sep 16 self-modification research) without adding the host here.
    Opens first try; posts are dated. Sweep `/research` every run._
- **Transluce** — https://transluce.org/ (non-profit interpretability and agent-behaviour research). `cap` `atk`
  - _Added 2026-09-24. Transluce's tracing of rogue agent activity through the public scanning service urlquery is what
    surfaced the Australian Services Australia intrusion and the probing of the Australian Institute of Health and Welfare,
    the NSW Bureau of Crime Statistics and Research, Data USA and the University of New Mexico; the board reached it through
    BleepingComputer and ABC News. **The research pages render as metadata only to this fetcher** — two attempts on
    `/agent-activity` returned no body — so expect to cite a syndicating outlet and upgrade on an attended run._
  - _Correction 2026-09-29: `/agent-activity` **does** open, on a second attempt, and returns the full body — title, the nine
    authors, the September 23 date, the three dated hacking attempts, the scan counts and every caveat. The note above was
    written after two first-pass failures; the rule is retry before falling back. The item is now sourced to the primary._
- **Perplexity Secure Intelligence Institute** — https://www.perplexity.ai/hub/blog/. `cap` `atk` `def`
  - _Added 2026-09-29. Publisher of the SPACE red team, which is the only cross-vendor test of agent sandbox containment the
    board has seen: nine models given root inside the VM, ten sandbox platforms compared, and its own platform reported among
    the eight that could be bypassed. Opens on a second attempt. Treat its comparisons as `self-reported` — it is measuring
    competitors as well as itself — but the self-incriminating parts are why the research is citable at all._
- **Independent OpenAI-agent investigators (Kitts / Larsen / Von Arx and collaborators)** — per-incident sites:
  https://collusion.wiki (DseWiki takeover) · https://rubyhack.ai (RubyGems campaign). `cap` `atk`
  - _Added 2026-09-12. This group has now produced two board items, and both times the board learned of the
    work from press rather than from the site. Both domains have been provenance-blocked on every attempt,
    so expect to cite a syndicating outlet; the value of the entry is knowing to look for a new one-off
    domain when a fresh OpenAI-agent episode surfaces, rather than discovering it a day late._

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
- **DOE — CESER (Office of Cybersecurity, Energy Security & Emergency Response)** — https://www.energy.gov/ceser (the office's landing page carries a Latest News block) · department-wide listing https://www.energy.gov/listings/energy-news. Energy-sector cyber programs, grid AI work, and the AI-FORTS line of research. `def` `pol`
  - _Note: DOE was absent from this list until 2026-09-09, and the cost was measurable — the CESER/Sandia grid-detection item of Sep 3 did not reach the board until Sep 6 days later, and only because an OT trade outlet happened to carry it. `www.energy.gov/ceser/articles` and `/ceser/newsroom` both 404; use the two paths above._
- **National laboratories** — Sandia https://newsreleases.sandia.gov/ · Idaho National Laboratory https://inl.gov/news/ (the ICS/OT-security lab). Both publish cyber work directly rather than only through DOE. `def` `cap`
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
  - _Note added 2026-10-03, California. `oag.ca.gov/news` was provenance-blocked while **`oag.ca.gov/media/news`
    opened first try** and returned a dated listing covering several releases a day; the individual
    `oag.ca.gov/news/press-releases/<slug>` page then opened too. Use the `/media/news` listing to diff the day. This
    is how the Oct 1 investigative subpoena on OpenAI was found; note that the release says the subpoena was served
    "yesterday," so the service date and the announcement date differ by one day._
- **StateScoop** — state & local government technology and cyber news. https://statescoop.com/. `pol` `atk` `def`
- **MS-ISAC / Center for Internet Security** — state, local, tribal & territorial incident coordination. https://www.cisecurity.org/ms-isac. `atk` `def`
- **State cyber agencies & fusion centers** — when named in an event (e.g. California Cybersecurity Integration Center / Cal-CSIC). `def` `atk`

## 9. Joint & international advisory channels — `atk` `def` `pol`

Joint advisories arrive through the agency feeds in §6 (a CISA `AAxx-xxxA` advisory co-sealed
with NSA / FBI / DC3 / EPA / DOE and international partners). Watch these directly too:

- **UK NCSC** — https://www.ncsc.gov.uk/. `def` `pol`
- **EU — European Commission (Digital)** — https://digital-strategy.ec.europa.eu/ · **ENISA** https://www.enisa.europa.eu/. `pol` `def`
- **European Supervisory Authorities (EBA, EIOPA, ESMA) and the ESRB** — ESMA news https://www.esma.europa.eu/press-news · EBA press releases https://www.eba.europa.eu/publications-and-media/press-releases. `pol` `mkt`
  - _Added 2026-09-23. §9 covered the European Commission and ENISA but no financial-sector supervisor, and the cost was the usual one: the three ESAs' joint statement on ICT risks from frontier AI models (JC 2026 25, Jul 31) and the ESRB warning behind it (Jul 7) were fifty-four days old before this board saw them, and reached it through a law-firm summary rather than any listed channel — the source-gap signature the 2026-09-09 measurement identified. This is where EU financial regulators state supervisory expectations for frontier-AI cyber risk under DORA. Both hosts open first try and carry dated press releases linking the underlying documents._
- **Five Eyes partners** — Australia ASD/ACSC https://www.cyber.gov.au/ · Canada CCCS https://www.cyber.gc.ca/ · New Zealand NCSC https://www.ncsc.govt.nz/ (usually co-signed on the joint advisories). `atk` `def`

## 10. Vulnerability & CVE registries — verification (cross-lane)

Used to verify — never invent — a CVE, its CVSS or its status before it goes on the board.

- **CVE.org** — https://www.cve.org/ (is the CVE actually assigned?). 
- **NVD** — https://nvd.nist.gov/ (CVSS, status).
- **GitHub Advisory Database** — https://github.com/advisories (GHSA records).
- **VulnCheck** — https://vulncheck.com/blog (exploitation-in-the-wild data).
- **OpenCVE** — https://app.opencve.io/cve/ (record, description, affected version range, assigning CNA). Added 2026-09-13. cve.org and nvd.nist.gov had been unreachable to this board's fetcher for six consecutive runs, so no CVE had been checked against any registry in that time; OpenCVE mirrors the same records and opens normally. Use it as the fallback registry, not the first choice — it carries no CVSS where none has been assigned, and it is a mirror, so a discrepancy with cve.org is resolved in cve.org's favour.
- **CERT/CC Vulnerability Notes** — https://www.kb.cert.org/vuls/. Added 2026-09-13. The coordination record rather than the registry entry: it names the reporter, states whether the vendor responded and whether a patch exists, and is often the only account of a flaw in an unmaintained project. Opens normally. It is a primary, so prefer it to a press write-up of the same note.
- **DIVD CSIRT — case files** — https://csirt.divd.nl/cases/ (individual cases at `/cases/<CASE-ID>/`). Added
  2026-10-01. The coordination record rather than the registry entry, in the same role as CERT/CC above: each case
  page carries the CVE IDs, the affected and explicitly **non-exploitable** version ranges, a dated disclosure
  timeline and the credited researchers. DIVD is a CNA, so the case page is the assigning party's own record.
  **The `/cases/` index is provenance-blocked while individual case pages open first try** — the same
  index-blocked-article-open shape as BleepingComputer, so find the case ID with a `site:csirt.divd.nl` search and
  open the case page directly. This is what let the board move its DIVD intrusion card off press onto
  `DIVD-2026-00014`, and source the two Zammad zero-days to `DIVD-2026-00015`. Note it gives a patch *status* and
  upgrade advice but not always a fixed version number.

## 11. Markets / cyber-insurance — `mkt`

- **Insurance Business** — https://www.insurancebusinessmag.com/us/cyber/. `mkt`
- **AM Best** — https://news.ambest.com/. `mkt`
- **Carrier / broker / reinsurer primaries** when cited (Munich Re, Swiss Re, Lloyd's, CFC, Coalition, Chaucer/Armilla, AIG, Berkley) — use the primary; carrier/broker marketing is `self-reported` unless a regulator, court or loss report says otherwise. `mkt`
- **Research reports** — IBM Cost of a Data Breach, ISO filings/endorsements. `mkt`
- **Funding & M&A trackers** — Crunchbase News cybersecurity https://news.crunchbase.com/sections/cybersecurity/ · TechCrunch security https://techcrunch.com/category/security/. The lane's capital half (rounds, valuations, acquisitions) arrives here first and rarely reaches a carrier or broker primary at all; without a standing sweep these land on the board four to six days late, as Upwind's $300M did on 2026-09-08. `mkt`

## 12. Press — the discovery pass (cross-lane)

**Sweep this tier first, before §1–§11.** Its job is to tell a run *what happened* in the window;
the primary sweep's job is to *source* it. Nothing here is a citation while a primary can be
opened — see the rule in "How to use it" above, and `DAILY_RUN.md` step 3.

Why this tier exists: until 2026-09-09 the scan list named no press outlet at all, even though
these are the outlets the board falls back to every time a lab or vendor primary is
provenance-blocked. With no defined starting point, the daily sweep depended on whichever roundup
a run happened to open, which is how the 2026-09-06 run produced eight items and **none** from the
fresh window.

- **Help Net Security** — https://www.helpnetsecurity.com/. Daily volume, week-in-review on Mondays. Strong on AI-security research write-ups.
- **SecurityWeek** — https://www.securityweek.com/ · AI section https://www.securityweek.com/category/artificial-intelligence/.
  - _Note added 2026-09-26: the Friday **"In Other News"** roundup is the single most productive discovery item this list
    has. On 2026-09-26 it surfaced four of the run's eight items — CARBONATO, the MemTensor worm, BragJack and the
    SpyCloud water census — each with the research primary's own URL, while the section indexes above were
    provenance-blocked. Search `site:securityweek.com "In Other News"` plus the week's dates and open the roundup itself
    rather than the index._
- **The Hacker News** — https://thehackernews.com/ · AI label https://thehackernews.com/search/label/artificial%20intelligence.
- **BleepingComputer** — https://www.bleepingcomputer.com/. Fastest on active exploitation and vendor advisories.
  - _Note added 2026-09-30: its **article** pages open on the first try even when the index is provenance-blocked,
    which it has been on five consecutive runs. Find the slugs with `site:bleepingcomputer.com` plus the date or
    the story, then open the article itself. It is also the only outlet this run found carrying DIVD's fuller
    account of the agent-run intrusion against it, which DIVD published on LinkedIn and nowhere openable._
- **The Record (Recorded Future News)** — https://therecord.media/. Strong on government, nation-state and policy.
- **CyberScoop** — https://cyberscoop.com/. Strong on US federal and agency action.
- **Cybersecurity Dive** — https://www.cybersecuritydive.com/.
- **Dark Reading** — https://www.darkreading.com/.
- **Industrial Cyber** — https://industrialcyber.co/. The OT/ICS beat, including a daily OT news roundup. This is the outlet that surfaced the DOE/Sandia item the government sweep had missed.
- **Axios** — https://www.axios.com/technology. Frequently first on AI-lab governance and policy moves.
- **Reuters** — technology and cyber desks. _Note: reuters.com has refused automated fetchers on every run that tried it; expect to reach its reporting through a syndicating outlet._
- **South China Morning Post** — https://www.scmp.com/tech · China politics https://www.scmp.com/news/china/politics. _Added 2026-09-14. The scan list had no route to Chinese official statements at all: §1–§11 cover Chinese labs but no Chinese state or Party channel, and the Cyberspace Administration of China's own journal `China Cyberspace` is not openable to this fetcher. SCMP reports those statements in English within a day and opens first try — it is how the state security minister's naming of Claude Mythos and GPT-5.5-Cyber reached this board. Press, so still a fallback: cite the Chinese primary whenever one can be opened._

Two cautions carried over from `RUNBOOK.md`. Watch for content-farm embellishment, which shows up
as an oddly precise number attached to a real story — several sites in the search results for any
given day are AI-generated rewrites of the outlets above, and they invent figures. And where two
outlets give a figure differently, neither is the primary: say so on the card and record it in
`judgmentNote`, as the 2026-09-09 Patch Tuesday item does.

---

## Extending this list

Add a source under the heading that fits it, with its **primary** URL and a lane tag or two.
Keep the primary-source-first rule: prefer a research blog, an agency page or a lab post over
an aggregator. When a source stops publishing or moves, replace or remove its line in the same
edit rather than leaving a dead link. This file is documentation only — changing it never
touches the build or the layout.
