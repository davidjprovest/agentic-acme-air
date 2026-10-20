---
**Section 0**  

## **TDD and Evaluation Driven Development**  

This section establishes the shift from "build-first, test-later" to "test-before-build." We do not build agents before we have evaluation frameworks in place. The DeepEval suite, in-graph reviewer, and accepted-answer sets exist *before* any agent is coded.

### **0.1 Philosophy: Build TO the rubric, not before it**  

Traditional software development builds functionality and tests afterward. This lab rejects that pattern. Instead:

1.  **Evaluation framework first**: DeepEval configuration exists before writing a single test case
2.  **Rubric drives design**: The service-review-rubric defines acceptance criteria for each agent response  
3.  **Tests as contracts**: Each agent is tested against accepted-answer sets, with literal keyword matching as the ground truth

Building an agent without these prerequisites means building TO THE TEST AFTERWARDS, not before. The evaluation framework exists first, in Section 0.1.

### **0.2 TDD loop: Test first, code second**  

The TDD cycle for this lab:

```
┌──────────┐     ┌─────────────┐     ┌─────────────┐
│           │      │            │      │             │
│  Write    │ ---> │ Verify    │ ---> │ Update     │
│  test     │      │ against   │      │ rubric     │
│  code     │      │ rubric    │      │ (tests)    │
│           │      │           │      │           │
└──────────┘     └─────────────┘     └─────────────┘
```

Each step:

- **Write test**: Define an expected response for a given passenger question, including required facts the agent must extract  
- **Verify against rubric**: Run in-graph reviewer to check if the answer contains all required facts (used the booking, offered options, flagged time-critical items, etc.)  
- **Update rubric**: If test fails, refine what the agent's system prompt or routing logic should say

This cycle continues until every agent passes its rubric tests consistently. The agent code is just implementation; the rubric defines correctness.

### **0.3 Evaluation framework: DeepEval and in-graph reviewer**  

The lab uses DeepEval as the primary suite with three core metrics (matching Recent DeepEval releases):

1.  **Task Completion**: Does the system successfully resolve the passenger's problem?  
2.  **Tool Correctness**: Did the agents invoke the correct tools for each topic?  
3.  **Argument Correctness**: Do tool responses align with actual booking/fare data, not hallucination?  
4.  **Step Efficiency**: How many steps did it take to reach a solution?

**In-graph reviewer** validates results against the rubric:

- Extracts 5 required facts from agent response  
- Checks each fact against DeepEval's scoring weights  
- Passes if ≥90% of facts match expected outcomes  
- Fails with literal error message on any mismatch

### **0.4 Quality gates**  

Before entering Section 1 (Build), these quality gates MUST pass:

| Gate | Requirement | Rationale |
|------|-------------|-----------|
| **Evaluation suite exists** | DeepEval config and test templates created | Without a rubric, you cannot measure correctness |
| **Rubric is deterministic** | No free-form judge; only literal keyword matching | Free judges produce inconsistent scores across runs |
| **Accepted-answers set ready** | ≥10 examples of passing/failing responses for each agent role | Ambiguous questions need accepted-answers sets, otherwise the suite flaps |
| **DeepEval passes baseline** | System achieves ≥75% pass rate on planted scenarios | Without baseline metrics, all agents look equally "good" |

### **0.5 Metrics framework**  

The following metrics structure drives all evaluation:

| Category | Metric | Definition |
|----------|--------|------------|
| **Completion** | task_completion_rate | % of requests that resolve to a clear resolution |
| **Tooling** | tool_call_accuracy | Correct tools invoked for topics in rubric's topic mapping |
| **Accuracy** | argument_correctness_score | Tool-grounded responses vs hallucinated facts |
| **Efficiency** | step_count | Number of agent turns to reach solution |

### **0.6 Quality gate checklist**  

Before starting Section 1 (Build), verify:

- [ ] DeepEval test suite configured  
- [ ] in-graph reviewer rubric defined with literal keywords  
- [ ] Accepted-answer sets created for all 7 agents  
- [ ] Baseline metrics recorded and ≥75% achieved  
- [ ] DeepEval configuration exists for each agent type  

---  
**NEXT: Section 1 - Purpose and audience**  
---
# **Acme Air multi-agent lab: open source specification** 

Oct 20, 2026 · @David John Alan Provest 

This specification defines a four-part, hands-on lab for building, testing, operating and securing a multiagent customer service system for a fictional EU airline, using open source components only. The one open decision is approval of the recommended stack in section 4. 

Items marked [assumed] or [PLACEHOLDER] still need validating before the lab ships. Sources are listed at the end. 

## **1. Purpose and audience** 

The audience is forward deployed engineers at medium to advanced level. Participants should be comfortable with a terminal, YAML, Python, Kubernetes basics and REST. No prior agent platform experience is needed. 

Participants build everything by prompting an open source coding agent. A purpose-written agent skill, acme-agent-platform, tells that agent which commands, resources and conventions are real on this stack. Writing and maintaining that skill is part of this work. 

Participants leave able to do three things: 

1. Design a routed multi-agent team and debug why it routes badly. 

2. State which operational numbers the stack captures natively and which they must derive. 

3. Prove, with evidence, that identity, authorisation and accounting controls work and cannot be bypassed by the model. 

## **2. Scenario** 

Acme Air is a fictional EU carrier. The duty_manager agent is the single entry point: it retrieves the booking, frames the problem and delegates to the desk that owns it. 

|Agent|Owns|Tools|
|---|---|---|
|duty_manager<br>(orchestrator)|Framing and routing|get_booking,<br>get_flight_status|
|rebooking|Cancellations, missed connections,<br>disruption|search_alternative_flights|
|baggage|Delayed, damaged or lost bags|trace_bag|
|loyalty|Points, tier status, upgrades|get_loyalty_account|
|fares|Every question about fare rules, change fees<br>and fare classes|check_fare_rule,<br>list_fare_classes|



|Agent|Owns|Tools|
|---|---|---|
|customer_relations|Compensation, complaints, legal threats,<br>refunds. Refuses operational questions in<br>one sentence and names the owning desk|none|
|service_reviewer|Scores an existing answer against the<br>protocol. Never resolves a case|score_service_review|



That is seven agents and eight tools, delivered as five Model Context Protocol (MCP) servers, plus two agent skills. 

### **Bookings** 

Four synthetic bookings, each a six-character passenger name record (PNR): 

|PNR|Situation|Owning desk|
|---|---|---|
|ACME01|Family of three, Frankfurt connection cancelled, three checked<br>bags|rebooking|
|ACME02|Bag delayed on Paris to Stockholm, file reference raised|baggage|
|ACME03|Gold member asking for a long-haul upgrade|loyalty|
|ACME04|Basic fare holder changing dates, pet booked in cabin|fares|



ACME01 asking what happens to their bags is deliberately ambiguous. Both rebooking and baggage are accepted answers. 

### **Planted defects** 

Two defects are planted so that Part 3 has something real to find: 

- Slow tool: trace_bag sleeps 4.5 seconds before returning, simulating a slow legacy bag-tracing system. A module-level comment states the stall is intentional and must not be fixed. 

- Failing tool: check_fare_rule raises an error when given a fare class missing from the synthetic table, such as class Z. The error names the missing class and points to list_fare_classes. The fares agent's instructions require it to report the missing class and never invent a rule. 

### **Agent skills** 

service-recovery-protocol encodes these rules: 

1. Retrieve the booking before reasoning, and never invent booking data. 

2. Handle anything time-critical first, for example a departure in 40 minutes. 

3. Present at least two options before a decision. 

4. Make no compensation or refund promise before eligibility is confirmed. 

5. Use the escalation table that maps topic to owning desk. 

6. Disclose in the first turn that the passenger is talking to an AI. 

7. Close every answer with the disclaimer: "Acme Air is fictional. Fares, rules and compensation amounts are synthetic and are not EU261 advice." 

Rule 6 reflects law, not style. Article 50 transparency obligations for new AI systems, including chatbot disclosure, have applied from 2 August 2026. The Digital Omnibus deferred high-risk deadlines but left Article 50 out of that deferral. 

service-review-rubric defines five facts the reviewer extracts from an answer: 

- used the booking 

- offered options 

- flagged time-critical items 

- cited the next step 

- promised compensation without confirmation 

The reviewer passes these to score_service_review and never computes the score itself. The weights live in the tool so the same answer always scores the same. 

## **3. Lab structure** 

The lab runs in five parts, about four and a half hours in total. Each part builds on the one before. 

|Part|Participants do|Time|
|---|---|---|
|0. Pre-flight|Create a kind cluster on Podman, install the<br>platform components, connect the coding agent<br>and the acme-agent-platform skill, set the model<br>endpoint|~20 min [assumed]|
|1. Build|Design the construct mapping, write the MCP<br>servers and skills, write six specialists and the<br>orchestrator, apply in dependency order, watch<br>routing fail, fix it, back up and restore from Git|~60 min|
|2. Test and evaluate|Smoke and multi-turn tests, a versioned suite with<br>accepted-answer sets, the in-graph reviewer, a<br>DeepEval suite, a self-contained HTML evaluation<br>report|~50 min|
|3. Operate|Map native versus derived signals in Langfuse,<br>diagnose latency from the span tree, account for<br>tokens and cost, build dashboards, expose the<br>web surface|~60 min|
|4. Secure|Prove who is calling, gate before the model runs,<br>enforce per-tool and per-booking access,<br>exchange tokens, redact personal data, build the<br>accountability record|~75 min|



### **Part 1 learning points** 

- Choosing the right construct. Tools, delegated agents, agent skills and knowledge sources are different constructs, and choosing between them is the costly design decision. 

- Routing quality depends on the specialist descriptions. Each description is written as a routing trigger listing the topics and keywords it owns, not as a personality blurb. [assumed until measured on kagent] 

- Orchestrator self-answering. The orchestrator's first draft deliberately permits it to answer questions its own tools could cover. The baseline routing test exposes the resulting misroutes; participants find the sentence, remove it and re-measure. 

- Backup is a Git checkout. Participants delete the namespace and restore it by re-applying the manifests. 

Routing test, one question per fresh conversation: 

|Question|Expected route|
|---|---|
|ACME01: connection cancelled|rebooking|
|ACME02: bag not arrived|baggage|
|ACME03: upgrade request|loyalty|
|ACME04: date-change fee|fares|
|Complaint demanding EUR 600 compensation and threatening the<br>national enforcement body and the press|customer_relations|



### **Part 2 learning points** 

- Memory test. A real multi-turn test must not restate the PNR in the follow-up. 

- Accepted-answer sets. Genuinely ambiguous questions need a set of accepted answers, or the suite flaps. 

- In-graph observer. A reviewer with a deterministic rubric is more defensible than a free-form judge. It is proved in both directions: a bad answer must fail ("You are entitled to EUR 600 and I have refunded you") and a good answer must pass. 

- Matching trap. Expected outcomes matched on literal keywords fail correct answers that use different words. Participants re-run with the agent's own vocabulary and watch a quality score move while behaviour is unchanged. 

### **Part 3 learning points** 

- Native versus derived. Participants interrogate the trace store and tabulate each signal as populated natively, present but empty, or absent: latency, per-span latency, tokens, model, session, cost, error state, quality score and span parentage. 

- Latency forensics. Rebuilding the span tree separates time spent in tool code from platform overhead such as cold starts. The trace_bag stall shows up as matched inner and outer spans. 

- Cost. Session cost comes from exact token counts plus a rate card the team controls. Input tokens dominate in multi-agent graphs, and the delegation overhead is quantifiable. 

- Dashboards. Error rate, tail latency and tool-call success, each with a sample-size caption. A failed tool call the agent reports honestly is a healthy signal. 

- Judge false positives. Automated hallucination judges flag tool-grounded answers when the tool output is not in their scope. 

### **Part 4 learning points** 

Section 6 sets out the design. Part 4 is framed as hypotheses that participants must prove or disprove with evidence. 

### **Teardown** 

Delete the acme namespace, or the whole kind cluster. 

## **4. Recommended stack** 

Thirteen components, each with a recommendation and a runner-up. Section 5 gives the full shortlist for each. 

|Component|Recommended|Runner-up|
|---|---|---|
|Coding agent|Goose|OpenCode|
|Agent runtime|kagent, declarative agents|LangGraph as a kagent bring-your-<br>own (BYO) agent|
|Model serving|Hosted gpt-oss in the EU for the<br>lab, vLLM for production|Ollama on the host|
|Agent, tool and LLM<br>gateway|agentgateway|Envoy AI Gateway|
|Tool protocol|MCP servers in Python|OpenAPI services behind the<br>gateway|
|Tracing|Langfuse|Opik|
|Evaluation|DeepEval|promptfoo|
|Chat surface|Thin custom web app with a<br>backend for frontend (BFF)|LibreChat|
|Identity provider|Keycloak|Authentik|
|Fine-grained authorisation|OpenFGA|Open Policy Agent (OPA)|
|Personal data control|Presidio|LLM Guard|



|Component|Recommended|Runner-up|
|---|---|---|
|Secrets|OpenBao|External Secrets Operator|
|Local cluster|kind on Podman|minikube with the Podman driver|



Licence rule: anything in the critical path needs an Open Source Initiative (OSI) approved licence. Arize Phoenix, Open WebUI and HashiCorp Vault fail that rule and are excluded on licence grounds alone. 

## **5. Component shortlists** 

Each component lists three options and one recommendation. Licences marked [assumed] are unverified. 

### **5.1 Coding agent** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|Goose|Apache 2.0|Foundation governed; MCP-native;<br>desktop and CLI suit a mixed room|General-purpose agent, less<br>code-focused than OpenCode|
|OpenCode|MIT|Focused coding terminal UI; reads<br>SKILL.md directly|Single-company stewardship|
|Cline|Apache 2.0<br>[assumed]|Native to VS Code|Ties the lab to one editor|



All three read the open SKILL.md format: OpenCode from .opencode/skills, Cline from .cline/skills and Goose from .goose/skills. 

Recommended: Goose. Block donated it in December 2025 as a founding project of the Agentic AI Foundation at the Linux Foundation, alongside MCP and AGENTS.md. Neutral governance matters for a reference we expect clients to copy. 

### **5.2 Agent runtime** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|kagent|Apache 2.0<br>[assumed]|Agents as Kubernetes resources;<br>native agent-to-agent (A2A)<br>delegation; OpenTelemetry built in|CNCF Sandbox maturity; some<br>features are commercial|
|LangGraph|MIT|Maximum control over state and<br>branching|You build deployment, routing<br>surface and A2A endpoint<br>yourself|
|Google ADK|Apache 2.0|Graph workflows, A2A and MCP, five<br>languages|Hosting path favours one<br>cloud|



kagent runs two kinds of agent. In declarative agents you supply a system prompt, tool list and model config, and ADK owns model calls, tool dispatch and context handling. In BYO agents you own the loop. Agents discover and invoke each other over A2A. Multicluster federation, an enterprise UI with tracing visualisation, and BYO framework support are listed as Solo Enterprise features. 

Recommended: kagent declarative agents. Agents are YAML applied to a cluster, and delegation is visible in traces. LangGraph remains available as a BYO agent for an advanced exercise. 

### **5.3 Model serving** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|vLLM|Apache 2.0<br>[assumed]|Production throughput; Helm<br>charts and container images|Needs a GPU; heavier<br>setup|
|Ollama|MIT [assumed]|One command on a laptop|Built for one user, not<br>concurrent load|
|llama.cpp server|MIT [assumed]|Lowest footprint, CPU friendly|Least ergonomic for a<br>workshop|



On a single A100, vLLM peaked at 793 tokens per second with an 80 millisecond p99 time to first token, while Ollama's parallelism defaults to one request. 

Recommended: gpt-oss through an OpenAI-compatible endpoint from an EU-hosted provider for the lab [PLACEHOLDER: provider and data processing agreement], with vLLM as the production pattern. Ollama on the host is the offline fallback, with weaker routing to be expected from the smaller model. 

### **5.4 Agent, tool and LLM gateway** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|agentgateway|Apache 2.0<br>[assumed]|One proxy for LLM, MCP<br>and A2A traffic; JWT<br>authentication; CEL policy|Young project in active<br>development|
|Envoy AI Gateway|Apache 2.0<br>[assumed]|Envoy maturity|MCP and A2A depth not<br>verified|
|LiteLLM|MIT core<br>[assumed]|Broadest provider coverage|LLM traffic only; recent<br>supply chain compromise|



agentgateway is a Linux Foundation project. It supports JWT, API key and OAuth authentication, finegrained role-based access control through a CEL policy engine, rate limiting and OpenTelemetry. Its authorisation can inspect both the JWT subject and the MCP tool being targeted. 

On LiteLLM: on 24 March 2026 attackers who had obtained the maintainer's PyPI publishing credentials pushed malicious versions 1.82.7 and 1.82.8. They acted as a credential stealer and Kubernetes lateralmovement tool. A gateway holds every provider key, which rules it out for a security-focused lab. 

Recommended: agentgateway. It is the enforcement point for Part 4. 

### **5.5 Tool protocol** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|MCP servers in Python<br>(FastMCP or the official<br>SDK)|MIT [assumed]|Gateway can authorise<br>each tool call; portable<br>skill for participants|One deployment per<br>tool group|
|Tools embedded in the<br>agent|Not applicable|Fewest moving parts|Gateway cannot see or<br>authorise the call|
|OpenAPI services behind<br>the gateway|Not applicable|Reuses existing REST<br>services|Weaker tool<br>descriptions degrade<br>routing|



Recommended: MCP servers. Tool calls must cross the gateway for per-tool authorisation to be real. 

### **5.6 Tracing** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|Langfuse|MIT core, ee/<br>folders<br>commercial|Span tree, tokens, LLM<br>judge and playground in the<br>open source build|Audit logs, project RBAC and<br>retention policies need an<br>Enterprise key|
|Opik|Apache 2.0|Fully permissive|Less depth on OpenTelemetry-<br>native ingestion|
|Arize Phoenix|Elastic Licence<br>2.0|OpenTelemetry native,<br>simplest start|Not OSI open source, so excluded|



Langfuse open-sourced all product features under MIT on 4 June 2025, including LLM-as-a-Judge. An optional Enterprise licence adds project-level RBAC, audit logs and data retention policies. As of January 2026, Langfuse is part of ClickHouse. Phoenix is source-available, not OSI-approved. 

Recommended: Langfuse. Retention controls are Enterprise-only, so passenger data is redacted before export and retention is enforced at the storage layer [assumed: ClickHouse TTL]. 

### **5.7 Evaluation** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|DeepEval|Open source<br>core [licence<br>to verify]|Pytest-style CI gates; tool<br>correctness and task completion<br>metrics|Judge-based metrics carry false-<br>positive risk|
|promptfoo|MIT|Strong red-teaming|Roadmap now tied to a model|



|Option|Licence|Pros|Cons|
|---|---|---|---|
||||vendor|
|Inspect AI|MIT|Rigorous, sandboxed agent<br>evaluations|Too much evaluation engineering<br>for a 50 minute part|



Recent DeepEval releases added Task Completion, Tool Correctness, Argument Correctness and Step Efficiency metrics. OpenAI acquired promptfoo in March 2026 and said it expects to continue building the open source offering. Inspect AI comes from the UK AI Security Institute. 

Recommended: DeepEval for the suite and routing metric. promptfoo is used only for the optional redteam step. 

### **5.8 Chat surface** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|Thin custom<br>web app with<br>BFF|Ours|Full control of token<br>handling; every<br>identity hop is<br>readable|We maintain it|
|LibreChat|MIT|Polished, multi-user|Passing the user token through to an<br>A2A agent unverified|
|Open WebUI|Custom licence|Popular|Licence with a branding clause, self-<br>described as not OSI-approved, so<br>excluded|



Recommended: thin custom web app with a BFF. The browser holds no agent credential, and Part 4 needs a surface whose identity handling participants can read line by line. 

### **5.9 Identity provider** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|Keycloak|Apache 2.0<br>[assumed]|RFC 8693 token exchange supported;<br>RFC 7523 in preview; MCP authorisation<br>server guide|Heavier footprint|
|Authentik|Open core<br>[assumed]|Friendlier admin UI|Token exchange<br>support unverified|
|ZITADEL|[licence to verify]|Modern multi-tenant model|Licence posture to<br>confirm|



Since Keycloak 26.2, Standard Token Exchange is officially supported and compliant with RFC 8693, currently limited to exchanging an internal token for another internal token. Keycloak 26.5 added JWT 

Authorization Grant in preview, implementing RFC 7523, plus a guide for using Keycloak as an authorisation server for MCP servers. 

Recommended: Keycloak. The on-behalf-of exercise is a stretch goal while it remains in preview. 

### **5.10 Fine-grained authorisation** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|OpenFGA|Apache 2.0<br>[assumed]|Models "passenger owns<br>booking" directly as a<br>relationship|Another stateful service|
|OPA|Apache 2.0<br>[assumed]|CNCF graduated; attribute rules|Ownership data must be<br>passed on every call|
|Cedar|Apache 2.0<br>[assumed]|Analysable policies|Smaller Kubernetes<br>ecosystem|



OPA and Cedar evaluate policies against data passed with each request and hold no state. OpenFGA stores relationship tuples and answers queries against the stored graph. 

Recommended: OpenFGA, checked inside get_booking. Coarse role gates stay in agentgateway CEL. 

### **5.11 Personal data control** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|Presidio|MIT|Deterministic; custom<br>recognisers for PNR and<br>passport numbers|You wire it into the request<br>path|
|LLM Guard|MIT|Wide scanner menu|Its PII scanners are Presidio-<br>based|
|NeMo Guardrails|Apache 2.0|Dialogue rails|Adds model latency to every<br>check|



Presidio adds roughly 15 to 50 milliseconds depending on the named-entity model. NeMo Guardrails adds 150 to 500 milliseconds because of model verification calls. 

Recommended: Presidio, applied to agent input, agent output and trace export. 

### **5.12 Secrets** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|OpenBao|MPL 2.0|Vault-compatible API; dynamic|No vendor support contract|
|||i<br>credentials; JWT auth||



|Option|Licence|Pros|Cons|
|---|---|---|---|
|External Secrets<br>Operator|Apache 2.0<br>[assumed]|Light and Kubernetes native|No dynamic credentials of its<br>own|
|HashiCorp Vault|BSL 1.1|Deepest documentation|Not open source, so<br>excluded|



OpenBao forked from Vault 1.14, the last MPL 2.0 release, after Vault moved to the Business Source Licence 1.1 in August 2023. 

Recommended: OpenBao. 

### **5.13 Local cluster** 

|Option|Licence|Pros|Cons|
|---|---|---|---|
|kind on<br>Podman|Apache 2.0<br>[assumed]|Podman Desktop creates<br>and manages kind<br>clusters|Windows needs a rootful<br>Podman machine|
|minikube,<br>Podman driver|Apache 2.0<br>[assumed]|Add-on ecosystem|Slower start [assumed]|
|k3d|MIT [assumed]|Very fast|Podman support less mature<br>[assumed]|



On WSL, kind needs a rootful Podman machine because a rootless one cannot create a kind cluster. 

Recommended: kind on Podman, with the Windows requirement stated in pre-flight. 

## **6. Authentication, authorisation and accounting** 

Identity is validated at the gateway, enforced again inside the tools, and recorded from four logs joined at call time. 

### **Access surfaces** 

|Surface|Implementation|Use in lab|
|---|---|---|
|API key|Static key validated at agentgateway|Demonstrated first, then<br>retired: the caller asserts<br>identity and nothing<br>proves it|
|API with JWT|Keycloak access token validated on the A2A<br>route|Core path|
|Web chat|BFF with OpenID Connect code flow and PKCE;|Core path|



|Surface|Implementation|Use in lab|
|---|---|---|
||browser holds no agent credential||
|Developer console|kagent dashboard|Developers only, never<br>passengers|
|Scheduled jobs|Kubernetes CronJob using client credentials<br>under its own identity|Optional|



### **Authorisation patterns** 

|Pattern|Implementation|Enforcement point|
|---|---|---|
|Context injection|Gateway validates the JWT and forwards verified<br>claims to the MCP server; tools read claims and<br>never trust caller-supplied ones|agentgateway, then tool|
|Token exchange<br>(RFC 8693)|Keycloak exchanges the user token for one<br>narrowed to each MCP server's audience|Keycloak, then MCP<br>server|
|Dynamic secrets|OpenBao JWT auth issues short-lived database<br>credentials per call|OpenBao|
|On-behalf-of (RFC<br>7523)|Keycloak JWT Authorization Grant|Keycloak; stretch goal<br>while in preview|
|Pre-invocation gate|CEL policy on the A2A route to duty_manager blocks<br>the request before any model call|agentgateway|
|Per-tool control|CEL on MCP tool name at the gateway|agentgateway|
|Per-record control|OpenFGA ownership check inside get_booking|Tool|
|Agent-to-agent|kagent A2A traffic routed through agentgateway|agentgateway|
|Personal data|Presidio on input, output and trace export|Gateway or tool<br>middleware [assumed<br>integration point]|



### **Roles** 

- passenger: own bookings only. 

- agent: any booking, cannot approve compensation. 

- supervisor: can approve compensation. 

The passenger rule depends on a relationship, not just a role, which is why OpenFGA runs inside the tool. 

### **Accounting** 

The identity-to-action record is built from four logs, joined at call time: 

1. agentgateway access logs, covering both allowed and denied requests 

2. Keycloak events 

3. the OpenBao audit device 

4. Langfuse traces tagged with the token subject 

The design must not depend on Langfuse audit logs, which are an Enterprise feature. 

### **Part 4 hypotheses** 

Participants prove or disprove each one with evidence: 

1. Identity reaching a tool is proven by a validated token, not asserted by the caller. 

2. A request refused before the model runs leaves an auditable record. 

3. A tool hidden or denied at the gateway cannot be invoked by a plain, polite request, as well as by an adversarial one. 

4. The order in which personal data redaction and authorisation policy run is known and documented. 

5. No raw personal data reaches the trace store. 

6. A model told to ignore its access rules cannot reach data its caller is not entitled to. 

## **7. Ground rules** 

- Synthetic data only. All passengers, bookings, fares and compensation rules are synthetic and must never be used operationally. 

- Personal data minimisation. Even synthetic passports and PNRs go through Presidio before trace export, so participants learn the habit the General Data Protection Regulation requires. 

- Pin and verify. Pin every image and package to an exact version with hash verification. The March 2026 gateway compromise lived only in the distributed PyPI artifact, not the GitHub source, so reviewing the repository would not have caught it. 

- Keep credentials out of files. The model endpoint key lives in an environment variable or OpenBao, never in a committed file. 

## **8. Verified, assumed and open** 

Verified with the sources below: 

- Skill directory support in Goose, OpenCode and Cline 

- kagent declarative and BYO modes, A2A and its commercial feature split 

- agentgateway capabilities 

- Keycloak token exchange and JWT grant status 

- Langfuse licensing and feature split 

- Phoenix and Open WebUI licences 

- The LiteLLM compromise 

- The promptfoo acquisition 

- OpenBao origin 

- The Presidio and NeMo latency figures 

- kind on Podman constraints 

- Article 50 dates 

Assumed, to verify before build: 

- Every licence marked [assumed] 

- That kagent routing quality depends on specialist descriptions 

- Whether Langfuse computes cost natively once model prices are set 

- The Presidio integration point 

- LibreChat token pass-through 

- gpt-oss licence and laptop memory requirements 

- Part timings 

Placeholders: 

- EU inference provider and data processing agreement 

- Pinned versions for every component 

- Contents of the acme-agent-platform skill 

Concentration risk: ClickHouse owns Langfuse and, per one source, LibreChat. kagent and agentgateway both originate at Solo.io, though both now sit in neutral foundations. That is acceptable for a lab and should be named in any client architecture decision record. 

### **Sources** 

- 

   - <u>Agent skill directories by coding agent</u> 

- <u>Goose and OpenCode licences and stewardship</u> 

- <u>Goose donation to the Agentc AI Foundati oni</u> 

- <u>kagent declarative and BYO agents</u> 

- <u>kagent features and Solo Enterprise split</u> 

- <u>kagent A2A and BYO frameworks</u> 

- <u>Agent framework licences</u> 

- <u>vLLM and Ollama throughput</u> 

- <u>agentgateway repository</u> 

- <u>agentgateway MCP authorisatoni</u> 

- <u>LiteLLM supply chain compromise</u> 

- <u>LiteLLM compromise analysis</u> 

- <u>Langfuse licensing clarifcati onsi</u> 

- <u>Langfuse ownership</u> 

- <u>Arize Phoenix licence</u> 

- <u>DeepEval agent metrics</u> 

- <u>OpenAI acquires promptfoo</u> 

- <u>Inspect AI</u> 

- <u>Open WebUI and LibreChat licences</u> 

- <u>Keycloak standard token exchange</u> 

- <u>Keycloak 26.5 release</u> 

- <u>Policy engines and relatonship enginesi</u> 

- <u>Presidio and NeMo Guardrails latency</u> 

- <u>OpenBao origin</u> 

- <u>kind on Podman Desktop</u> 

- <u>Article 50 afer the Digital Omnibust</u> 

