You said:
Need help building llm model router system

For now pareto seems fine to stsrt off, we'll discuss advancing it later.

A couple notes.

We will structure with 3 key pillars and both soft and hard constraint / optimization

Speed (conciseness needs to become a factor too, effectively average session time turns tok len so on)

Cost As blended in + out per 1m W caching and other optis factored In

And finally quality agsinst a given task via index built from benchmark scores

We have baseline hard constraints then optimize in order after all are met

I have subscriptions some with dynamically changing usage, others simply require complex scraping and math to gauage to a blended mtok.
Theres also providers who give seasonal changes e.g. 2x usage and other items as well as rotating free or cheap models and other similar complex factors.

Models and providers will be provided via structured elicitation let's assume, and some logic for budgeting over a month is given such that say a sub can be swapped with no sub, chealer/more exp or diff sub and other budgeting effectively trading commodity/resources to best optimize while at the per call level we perform a Complex per role pareto, e.g. Basic roles such as fast and.high as well..as specialized r.g. Doc writer

ChatGPT said:
Here’s a solid “Pareto-first” router design that won’t paint you into a corner when you later add bandits, learned predictors, seasonal pricing, and subscription arbitrage.

1. Core idea
   You have two optimization layers:
   Monthly / budget allocator (slow loop)
   Decides which subscriptions/plans/providers/models are “enabled” this month/week/day, with quotas + internal shadow prices.
   Per-call router (fast loop)
   Given a request + role + constraints, chooses the best model from the currently enabled pool, using hard constraints first, then Pareto / lexicographic optimization across:
   Speed (latency + “conciseness” proxy like expected output tokens / expected turns)
   Cost (blended in/out, caching, effective $/mtok under subscriptions)
   Quality (task score index from benchmarks + your internal evals)
   This separation is what makes subscriptions + scraping + seasonal bonuses manageable.
2. Data model (minimal but future-proof)
   2.1 Model + Provider catalog
   Each model option is not just “gpt-x”, it’s a routeable offer:
   offerId (unique)
   provider (OpenAI, Anthropic, Google, local, etc.)
   modelName
   contextWindow
   tooling capabilities (function calling, JSON mode, vision, etc.)
   pricing (in/out, cache read/write, batch discounts)
   limits (RPM, TPM, concurrency, max output tokens)
   reliability stats (timeouts, error rate)
   2.2 Subscription / plan abstraction
   You need a unified “effective marginal cost” interface.
   Represent each plan as a resource bucket:

planId
provider
billingPeriod (monthly)
fixedCost ($/month)
includedUsage (by model or by family; sometimes separate in/out)
multipliers (seasonal 2x, weekends, etc.)
priorityRules (some providers throttle after threshold)
swapOptions (upgrade/downgrade rules + effective start date)
Then produce a derived runtime object:
effectiveUnitCost(model, tokensIn, tokensOut, cacheStats) → dollars
remainingQuota(model) → tokens remaining (or “unlimited but throttled”)
shadowPrice(model) → internal $/token reflecting scarcity (key!)
Shadow price is how you convert “subscription scarcity” into per-call routing.
2.3 Task + Role schema
For each request you compute:
role (fast_chat, high_accuracy, doc_writer, code_review, e2e_test, etc.)
hardConstraints (must support tools? must be JSON? max latency? max cost?)
softWeights or priority order (lexicographic)
qualityTarget (minimum quality score or “top tier only”) 3) Scoring: hard constraints → Pareto → final pick
3.1 Hard constraint filter (non-negotiable)
Examples:
Must support tool calls / structured JSON
Must handle context length
Must meet p95_latency <= X (or at least predicted)
Must meet cost <= Y (worst-case token cap)
Must meet quality >= Qmin for role
Anything failing gets removed before optimization.
3.2 Predictors you need (can start dumb)
Per offer, per role:
latency_pred_ms (use rolling p50/p95 by provider+model+region; start with static)
output_tokens_pred (role-based heuristic: doc_writer > fast_chat)
turns_pred (optional; start with 1)
quality_pred (your index; see next section)
cost_pred = effectiveUnitCost + shadowPrice adjustment
3.3 Pareto frontier
Compute objective vector for each remaining offer:
Speed objective: (latency_pred_ms, output_tokens_pred, turns_pred)
You can collapse to one number if you want: session_time = latency + k*output_tokens + m*turns.
Cost objective: effective_cost_pred (includes cache + subscription shadow price)
Quality objective: -quality_pred (since we minimize)
Compute Pareto set (non-dominated). If that set is large, do tie-break.
3.4 “Optimize in order after all hard constraints are met”
If you literally mean lexicographic:
maximize Quality
then minimize Cost
then minimize Speed (or the other order you want)
Do it like:
Take top-K by quality (or within epsilon of best)
Among those, take cheapest (or within epsilon)
Among those, take fastest
This is stable and easy to reason about.
If you want “Pareto but with preferences”, use weighted Tchebycheff or epsilon-constraint, but lexicographic is fine to start.

4. Quality index that actually works
   You said: “index built from benchmark scores.” Do this:
   4.1 Create a normalized score per task family
   For each model, maintain:
   benchmarks: (MMLU, HumanEval, GSM8K, doc writing eval, tool use, etc.)
   Normalize each benchmark to 0–1:
   norm = (score - min) / (max - min) across your candidate set (or a fixed baseline set)
   4.2 Role → benchmark weights
   Examples:
   fast_chat: 0.5 instruction following + 0.3 safety/refusal quality + 0.2 coherence
   doc_writer: 0.4 writing eval + 0.3 instruction following + 0.3 long-context
   code_review: 0.5 coding + 0.3 reasoning + 0.2 tool use
   e2e_test_agent: 0.6 tool use + 0.4 planning/robustness
   So:
   quality_pred(role, model) = Σ w_i(role) \* norm_benchmark_i(model)
   4.3 Add “your reality” correction
   Benchmarks lie. Add:
   online_success_rate(role, model) from your own logs (pass/fail, user re-ask rate, etc.)
   penalty_for_refusal_mismatch (some models refuse too much)
   format_adherence_rate (JSON validity, schema conformance)
   Fold it in as a multiplier or additive term.
5. Subscriptions, scraping, seasonal bonuses: how to model cleanly
   5.1 Treat everything as a “token budget marketplace”
   At runtime you want one number: effective marginal cost per token (in/out/cache).
   That means your scraper + plan math should output:
   remaining_included_tokens by model family
   throttle_risk (soft cost)
   reset_time
   seasonal_multiplier
   5.2 Shadow pricing (the secret sauce)
   If a subscription has “included” usage, naive routing will burn it immediately. You need scarcity.
   A simple shadow price:

shadow = base_shadow \* (1 / max(remaining_ratio, ε))
remaining_ratio = remaining_quota / total_quota_this_period
so when you’re running out, shadow spikes → router stops using it unless it must.
If plan has “unlimited but throttled after X”, convert throttling probability to expected latency cost (or a penalty added to cost).
5.3 Monthly allocator (slow loop) output
Every hour/day:
Decide enabled offers
Set per-offer shadowPrice and maybe a maxSpendPerDay
Optionally set “reserve pools” per role (e.g., keep premium model tokens for high_accuracy only)
This lets you do “subscription swap vs no sub” as a deliberate choice, not chaos inside the per-call router. 6) Roles + policies (what you described: fast/high + specialized like doc writer)
Define “router profiles”:
Example profile:

doc_writer:
hard: context >= N, supports citations/tools? (if you need)
hard: quality >= 0.78
soft order: quality → cost → session_time
output_tokens_pred multiplier: 1.8x baseline
fast_chat:
hard: p95 latency <= 1500ms (or whatever)
soft order: speed → cost → quality (or speed → quality → cost)
high_accuracy:
hard: quality >= 0.9
soft order: quality → speed → cost (or quality → cost → speed)
You’ll end up with ~8–20 roles, not 200. Keep it tight. 7) Implementation skeleton (practical)
Components
Catalog service: offers + capabilities + base pricing
Plan service: scrapes usage, applies plan math, publishes effectiveUnitCost + quota + shadowPrice
Metrics service: latency/error stats by offer, updates predictors
Quality index service: benchmark table + online eval, publishes quality_pred per role
Router API (hot path): chooseOffer(request, role, constraints) -> offerId
Execution layer: handles retries/fallbacks + circuit breaker
Hot path algorithm (fast loop)
Parse request → role + constraints + estimate tokens
Candidate offers = enabled offers ∩ capability constraints
Filter by hard constraints (cost upper bound uses worst-case tokens cap)
For each candidate, compute (quality, cost, session_time)
Pareto prune
Lexicographic finalize (or your chosen order)
Execute with fallback policy:
If timeout/error → next best in Pareto set
If format invalid → retry once with same, then fallback to higher format-adherence model 8) What to build first (Pareto MVP)
If you want the smallest thing that’s still “real”:
Static catalog (JSON file) of offers + capabilities + raw pricing
One plan adapter that turns subscription into effective cost (even if rough)
Rolling metrics: p50/p95 latency + error rate by offer
Quality index v0 from public benchmarks + manual role weights
Router: hard filter + Pareto + lexicographic
Fallback: timeout/error + format failure
That gets you a working router fast. 9) The two hard problems you should not ignore
Token prediction
Cost and “conciseness” depend on output tokens. Start with heuristics per role, then upgrade to a learned predictor using prompt features + historical logs.
Subscription arbitrage correctness
If your effective marginal cost math is wrong, routing becomes random. Shadow prices + conservative assumptions (worst-case) prevent nasty surprises. 10) If you tell me your initial roles + constraints, I can give you the actual config layout
To move from design to something you can drop into a repo, you need a config format like:
roles.yaml (constraints + objective order + weights)
offers.yaml (capabilities + base price)
plans.yaml (plan rules + seasonal multipliers)
benchmarks.csv (raw scores)
If you paste your first-pass roles (even messy) and the list of providers/models you expect, I’ll write the exact schemas + a reference routing function (language of your choice: Go, Python, TS).

You said:
Do extensive deep research

Feb 2026 SOTA

Assume . monthly budget is 600

ChatGPT said:
To help with deep research on state-of-the-art (SOTA) LLM model routing systems as of February 2026, could you clarify a few points:
Are you primarily focused on:
Open source models only?
API-based models (like OpenAI, Anthropic, Mistral, Cohere, etc.)?
A mix of both?
What is your intended use case distribution across the budget? E.g.,
Real-time chat?
High-quality document generation?
Coding or agent tasks?
Or others?
Should we evaluate models in terms of available subscriptions under $600/month including all in/out token pricing and allowances?
Are there any existing tools or orchestration frameworks you're leaning toward (e.g., OpenRouter, vLLM, LoRA-enabled inference, etc.), or should I include comparisons of orchestration layers too?
Do you want benchmark-based quality comparisons per model or per provider-plan-bundle (since some offer special quotas, boosted usage, etc.)?
Let me know and I’ll begin the research right after.

You said:
Mix of both, self host via let's say gpu.rentsl is OK given it makes sense etc,

We use glm moonshot qwen gemini Claude code codex cursor copilot minimax and a variety of others as subscriptions atm w/openrouter and vercel ai gateway for general api access.

These are models for coding! So assume my average preferred model is haiku 4.5, or gemini 3 flash but both are subpar quality for more intense tasks

ChatGPT said:
Got it. I’ll do deep research on state-of-the-art LLM model routing systems and top-performing models for coding tasks as of February 2026, within a $600/month budget. This will include API-accessible models (via OpenRouter, Vercel AI Gateway, etc.) and viable self-hosting options (like GPU.rentals), factoring in current performance, pricing, token limits, and practical routing strategies.
I’ll report back with a comparison of available models, providers, subscription options, and recommendations for optimal routing setups tailored to coding use cases—especially those requiring higher-quality outputs than Haiku 4.5 or Gemini 3 Flash.
Research completed in 5m · 17 sources · 66 searches
State-of-the-Art LLMs for Coding (February 2026)
Top Code-Optimized LLMs in 2026 – Performance and Capabilities
Proprietary Frontier Models: The latest closed-source models lead many coding benchmarks. OpenAI’s GPT-5.2 is currently the top performer on code generation tasks, scoring ~89% on the LiveCodeBench benchmark. It comes in specialized variants like GPT-5.2 Codex, fine-tuned for structured coding, which excels at generating code given a clear spec. Anthropic’s Claude family also ranks highly. Claude Opus 4.5/4.6 delivers excellent deep reasoning, code review, and debugging performance (87% on LiveCodeBench), with a careful, planful style suitable for complex refactoring and multi-file understanding. Google’s Gemini 3 model suite is a strong contender as well – the Gemini 3 Pro model preview achieved a remarkable 92% on code generation benchmarks (LiveCodeBench), the highest of any model, while the lighter Gemini 3 Flash variant still scores ~91% and is tuned for high-speed Q&A and code completions. Newcomers are also on the frontier: MiniMax M2.5 (230B parameters, MOE architecture) has matched the coding prowess of the best from OpenAI/Anthropic on key developer benchmarks (e.g. ~80% on SWE-Bench, roughly on par with Claude Opus 4.6’s 80.8%). MiniMax achieves frontier-level coding ability despite its lower cost (as discussed below), making continuous AI pair-programming feasible. Another rising model is Moonshot AI’s Kimi K2.5, a multimodal coder with “agentic” tool use; it scores around 85% on code benchmarks (rivaling older GPT-4-tier models) and can incorporate visual context (e.g. UI screenshots) into coding tasks. In China’s open labs, Zhipu AI’s GLM-5 (successor to GLM-130B) is an open model that matches top proprietary models – the prior GLM-4.7 “Thinking” model reached 89% on LiveCodeBench, indicating that GLM-5’s reasoning-focused version is on par with GPT-5-level code performance. Cost-Effective and Specialized Models: Many tasks don’t require the absolute frontier model, and 2026 offers specialized coding LLMs optimized for speed or cost. Claude Haiku 4.5 (Anthropic) is a fast, low-drama coder ideal for iterative use. It provides ~73% accuracy on SWE-Bench (about 90% of the flagship Claude’s coding performance), but is 4–5× faster than Claude Sonnet 4.5 in latency. Haiku is the model you keep “always-on” for small requests – explaining errors, generating helper functions, or making minor edits – because it’s cheap enough to query repeatedly. Google’s Gemini Flash 3 is another value-oriented model; it has good instincts for code and UI tasks and can be run at high frequency with minimal cost/latency penalty. While its reasoning depth is lower than the Pro model, it still handles everyday code generation and Q&A well (often needing only occasional steering). Anthropic’s mid-tier Claude Sonnet 4.5 serves as a balanced “daily driver” model – it’s the default smart model in many coding tools with solid competence across the board. Sonnet excels at code explanation and following software design instructions, while Claude Opus 4.6 is invoked for the truly hard problems requiring an “hour of thought saved in one prompt”. OpenAI’s lineup similarly offers scaled choices (e.g. GPT-5.1 or earlier GPT-4.5 models) which, while slightly behind the absolute latest, still perform extremely well (~85–87% on code benchmarks) at lower price points. Open-Source and Self-Hosted Models: Impressively, the open-source community has pushed free code models to near state-of-the-art levels. DeepSeek V3.2, an open Mixture-of-Experts model (671B total params, ~37B active), demonstrates “frontier” coding ability at a fraction of the cost. It reportedly achieves 90%+ of top-model quality at roughly 1/10th the cost, even outperforming some closed models on complex coding tasks. Likewise, GLM-4.7/5 (MIT-licensed) reaches ~89% on code generation tests, meaning developers can self-host a model that’s virtually as good as GPT-5 on coding. Other open models fill various niches: Code LLaMA (Meta’s 34B code-tuned Llama2) and Qwen-14B/7B (Alibaba’s open models, with a specialized Qwen-Codecoder) are popular for local deployment. These models can be run on accessible hardware (single GPUs) and, with community fine-tuning, deliver strong coding help for everyday tasks. For instance, CodeLlama-34B or a Qwen-14B coder can handle basic code completions, small scripts, and act as a helpful “local Copilot” – all with zero token costs beyond the initial hardware investment. The gap between open models and closed APIs has dramatically closed; many open models now match or exceed older generation proprietary models. As one example, MiniMax M2.5 is technically “open-source” (weights not fully public yet, but available via an open API) and was the \*\*first open model to beat Anthropic Claude 4 on independent coding benchmarks】. In practice, these developments mean a savvy team can rely on open models for ~85–90% of coding needs, only calling on the most advanced proprietary model for the rarest tricky problem. Table 1: Comparative Performance of Selected Coding LLMs (Early 2026)
Model Provider Notable Coding Benchmarks Special Strengths
GPT-5.2 Codex OpenAI (proprietary) 89% LiveCodeBench; tops HumanEval/MBPP Precise code generation, complex architecture planning. Best raw code score.
Claude Opus 4.6 Anthropic (prop.) ~81% SWE-Bench; 87% LiveCodeBench Deep reasoning, safe refactoring, multi-file context. Excels at code review & debugging.
Gemini 3 Pro Google (prop.) 92% LiveCodeBench; >3400 Codeforces Elo UI-centric coding (great with front-end/UI tasks); dominant on algorithmic challenges. Large context.
MiniMax M2.5 MiniMax (open API) 80.2% SWE-Bench (≈Claude/GPT-5 parity); 76% BrowseComp “Frontier” code ability at low cost. Good tool use (office docs, web). 197K context.
Claude Haiku 4.5 Anthropic (prop.) 73.3% SWE-Bench; ~90% of Claude’s agentic score Fast (2–5× faster than larger Claude), low cost for iterative use. Ideal for quick fixes, error explanations.
Kimi K2.5 Moonshot (prop./open) ~85% LiveCode (est.); strong visual coding & agent tasks Multimodal (processes code + images). Self-directed “agent swarm” for complex multi-step problems. 262K context.
GLM-5 (Reasoning) Zhipu AI (open src) ~89% LiveCodeBench; near top on MMLU reasoning Open-source and near-SOTA performance. Designed for long-horizon coding and planning. 205K context.
DeepSeek V3.2 DeepSeek (open src) ~85–90% on coding evals (beats GPT-5.2 on some tasks) Open MoE model with tool-use integration. Very efficient – high quality per FLOP. Large context (supports long inputs).
Code LLaMA 34B Meta (open src) ~50% HumanEval (fine-tunes reach higher); good on Python tasks Fully self-hostable on 48GB GPUs. Strong at code completion and documentation drafting. Popular for offline IDE assistance.
Qwen-14B Coder Alibaba (open src) ~48% HumanEval (base); ~70% with finetune on benchmarks (est.) Lightweight (fits on a single GPU), fast for smaller tasks. Often paired with local dev environments.
(Benchmarks: LiveCodeBench = broad coding challenge suite (higher is better); SWE-Bench = comprehensive software engineering benchmark; Codeforces Elo = competitive programming skill rating. Context = max tokens model can handle in prompt + code.) As shown, multiple models now achieve around or above 85–90% on rigorous coding benchmarks, indicating they can correctly solve a large majority of programming tasks. The absolute leaders like GPT-5.2 and Claude/Gemini are approaching human-expert level on many coding challenges. However, the practical difference between a 85% model and a 90% model may be small for everyday coding – often it manifests in subtle reliability issues on extremely complex tasks. For most use cases, models like Claude Opus, Gemini, MiniMax, or GLM can capably generate and understand code across languages (Python, JavaScript, Java, C++, etc.) and handle tasks from writing unit tests to debugging tricky issues. The key is that developers now have a spectrum of LLMs to choose from, balancing raw capability against cost, speed, and specialization.
Provider Access and Pricing Comparison
Access to these models comes either via cloud APIs (often through multi-model platforms) or by self-hosting. Many top models are accessible through unified gateways like OpenRouter or Vercel AI, which aggregate multiple providers under one API. For example, OpenRouter supports 300+ models across 60+ providers (Anthropic, OpenAI, Google, MiniMax, Moonshot, etc.), while Vercel’s AI Gateway allows routing to popular APIs with a single integration (OpenAI, Anthropic, Replicate, etc.). These services generally charge per token usage at the model’s base price (with minimal or no markup) – essentially passing through the cost from the model provider. OpenRouter, for instance, shows the exact token prices from each vendor (and charges a ~5.5% platform fee on pay-as-you-go), whereas Vercel’s gateway charges the provider’s list price with zero markup (beyond a small free credit). The table below summarizes pricing and context limits for several notable coding LLMs as of Feb 2026 (in USD, per million tokens). “Input” cost refers to prompt tokens and “output” cost to generated code tokens. For reference, 1M tokens is roughly 750K words (about 1,500 pages of code). Table 2: Access and Pricing for Selected Coding Models (Feb 2026)
Model (Provider) Max Context Cost per 1M Input Tokens Cost per 1M Output Tokens Access Availability
Claude Haiku 4.5 (Anthropic) 100K tokens $1.00 $5.00 Anthropic API, Bedrock, Claude.ai UI.
Claude Opus 4.6 (Anthropic) 1,000K tokens $5.00 $25.00 API (Anthropic Enterprise), via OpenRouter.
Claude Sonnet 4.5 (Anthropic) 1,000K tokens $3.00 $15.00 API (Anthropic), OpenRouter, ChatClaude Pro.
GPT-5.2 Codex (OpenAI) 128K tokens (est.) $1.75 $14.00 OpenAI API (preview), via Azure OpenAI.
GPT-5.2 “Pro” (OpenAI) 256K tokens $21.00 $168.00 OpenAI API (limited beta).
Gemini 3 Flash (Google) 1,050K tokens $0.50 $3.00 Google Vertex AI, OpenRouter (Preview).
Gemini 3 Pro (Google) 1,000K+ tokens $2.00 (est.) $12.00 (est.) Google Early Access (Ultra tier).
MiniMax M2.5 (MiniMax) 197K tokens $0.30 $1.10 OpenRouter, MiniMax API (OpenHands).
MiniMax M2.5 Lightning 197K tokens $0.60 (2× std.) $2.40 MiniMax API (faster inference mode).
Moonshot Kimi K2.5 262K tokens $0.23 $3.00 OpenRouter, Moonshot AI API.
Zhipu GLM-5 (open-source) 205K tokens self-host (no token fee) self-host (no token fee) Download (MIT license); Hosted via Z.ai or Vercel.
DeepSeek V3.2 (open-source) 256K tokens (sharded) self-host self-host Download (open weights); also on Vertex AI.
Code LLaMA 34B (open-source) 100K tokens (with RoPE) self-host self-host Download (Meta license); community API on Replicate.
xAI Grok Code 1 (xAI) 256K tokens $0.20 $1.50 xAI API (Beta), OpenRouter.
Trinity-XL (Arcee) (open) 131K tokens $0.00 $0.00 OpenRouter free tier (open model).
Notes: Pricing is per 1M tokens (input=prompt, output=completion). “Self-host” means no token fees – cost is in compute (GPU hours). Free models like Trinity or Step 3.5 are community-driven LLMs available at no cost on aggregator platforms. Context length varies; ultra-high context (1M token) models can ingest entire codebases or large documents in one go, but those models are generally proprietary (e.g. Anthropic, Google) and require premium access. Many open models support 100K+ tokens via efficient attention mechanisms or by sharding context over multiple passes. From the table, we see wide differences in token pricing. The most advanced models (e.g. GPT-5.2 “Pro”) are extremely costly – up to $168 per million output tokens – which can translate to ~$0.168 per 1,000 tokens, or roughly $0.012 per line of code. In contrast, newer entrants like MiniMax M2.5 have slashed the price of frontier coding models by 95%. MiniMax’s standard model costs only $1.10 per M output tokens (i.e. $0.0011 per 1K tokens, 20× cheaper than Claude Opus or GPT-4/5). This radical price reduction means that, for example, running a coding agent continuously 24/7 becomes financially feasible: one could operate an AI pair-programmer “around the clock” for roughly $1/hour (≈$720/month) using M2.5, whereas using Claude or GPT for the same would have cost $10–20/hour. Similarly, Anthropic’s introduction of Claude Haiku 4.5 drove costs down – Haiku is 66% cheaper per token than Claude 4’s previous model (and ~10× cheaper than Claude 4.5 was at launch). Competition has also pushed OpenAI to offer a specialized Codex model of GPT-5.2 at much lower rates (only ~$14/M out vs $168/M for the full model), making it viable for heavy code generation workloads. In practical terms, API users often mix and match these models via routing services. OpenRouter (pay-as-you-go) makes it easy to call, say, Claude Haiku for quick prompts and switch to Claude Opus or GPT-5 when needed – all under one API key. It charges no markup on the underlying token prices (just the ~5.5% fee on total usage), and even offers a free tier (community models only, 50 requests/day) for experimentation. Vercel AI Gateway similarly has a free ~$5 credit each month for LLM calls, after which you pay exactly the provider’s rates for tokens. The key difference is that Vercel’s costs also include any cloud function execution time (since it’s tied to Vercel’s hosting), whereas OpenRouter purely bills for the LLM tokens. Both platforms allow “Bring Your Own Key” (BYOK) as well – you can use your own OpenAI/Anthropic API keys through their routing layer, which then typically incurs no platform fee but uses your provider quota. For self-hosting, pricing shifts from per-token to infrastructure costs. Running an open 30B–70B model on a cloud GPU might cost on the order of $0.50–$2.00 per hour of GPU time. For example, renting an A100 40GB for one hour (~$1.50/hr) can generate on the order of 0.5–1 million tokens of output (depending on model speed), implying an equivalent token cost of roughly $1.50–$3.00 per million – already far below the fees of top proprietary models. If utilization is high, owning or renting GPUs becomes cost-effective. Some services like Replicate offer hosted inference for open models, but note that third-party platforms often charge a premium (e.g. some Replicate endpoints effectively cost $0.015 per 1K tokens or more, depending on model speed) – which can end up 10× the cost of native APIs for comparable output. Thus, power users with >100M tokens of monthly usage often consider running open models on dedicated hardware to stay within budget.
Cost-Efficiency Strategies (Maximizing Quality Under a $600/Month Budget)
With many model options and pricing tiers, a key challenge is optimizing for cost while meeting quality needs. A $600/month budget, while significant, can be quickly consumed by careless use of the largest models. Below we outline practical strategies to get the most coding assistance for the money:
Choose Models by Task Complexity: Use cheaper, smaller models for simpler tasks and reserve the expensive models for truly hard problems. For example, for everyday Q&A, boilerplate generation, or unit test writing, one might call Claude Haiku or Gemini Flash (costing ~$0.001–$0.005 per 1K tokens). Only when faced with a complex algorithm design or a tricky bug that the smaller model struggles with would you escalate to Claude Opus or GPT-5. By routing easy queries to Haiku and only escalating on demand, teams can handle the bulk of requests cheaply and stay within budget. Academic research on LLM routing shows that even a simple two-model router can cut costs by ~75% while retaining ~95% of top-model quality, by sending easy queries to a weaker model and only hard queries to the strongest model.
Leverage Subscription Plans and Quotas: Take advantage of any fixed-cost subscriptions for interactive use. For instance, ChatGPT Plus ($20/month) includes GPT-4.5 or GPT-5 access via the ChatGPT UI, which can cover ad-hoc coding questions and debugging without eating into your API budget. Similarly, Anthropic’s Claude Pro plan (if available) provides a certain number of Claude 4.5 prompts in their Claude.ai interface. These UIs often have generous usage limits that would be expensive if done via API. Using them for “consultation” style tasks (like discussing architecture or reviewing a code snippet) can offload work from your paid API calls. GitHub Copilot is another subscription ($10/month) that, while not an LLM you query directly, provides AI code autocompletion continuously in your IDE. Copilot is powered by OpenAI models (now GPT-4 or specialized Codex models for code), and its fixed monthly price can replace many small completion requests you might otherwise send to an API. In a budget-conscious setup, you might use Copilot for live coding assistance and only call an API when you need a large block of code or detailed analysis.
Mix Free or Open-Source Models for Volume: Many teams adopt a hybrid approach – e.g. using an open-source code model locally for iterative development, and only calling an API for final validation or when the open model falls short. If you integrate an open model (like Code LLaMA or GLM-5) into your toolchain, the per-token cost is essentially $0 (aside from infrastructure). You could run a local instance on a rented GPU during work hours for perhaps $300/month, handling the majority of completions and tests, and still have $300 left to spend on occasional calls to GPT-5 or Claude Opus for their superior reasoning on tough problems. This way you stay under $600 but get the “best of both”: high throughput from the local model and peak quality from the cloud when needed. As an example, one might use an open model to draft a large portion of a module (cheaply generating, say, 100K tokens of code), then use a single GPT-5 call to review or optimize that code – incurring maybe $2 of API cost. The initial draft cost essentially nothing, dramatically reducing overall spend.
Use Routing/Orchestration Tools: Modern “meta AI” frameworks can automate the above decisions. Tools like OpenRouter’s auto-routing and budget policies allow you to set rules – for instance, try a prompt on a free model first, and if the confidence or result isn’t good, automatically retry with a stronger model (failed attempts aren’t billed under its policy). This ensures you only pay for the Claude/GPT call when absolutely needed. Third-party open tools like GPTRouter (by WriteSonic) enable custom routing logic in your app: you can programmatically route short/simple prompts to a fast model and long/critical prompts to a powerful model. GPTRouter even provides latency and cost observability, so you can fine-tune the thresholds that trigger an upgrade. By continuously analyzing usage, you might discover, for example, that 70% of your requests could be handled by a 7B model, and only 30% truly need the 70B model – yielding huge savings. Automated routing is akin to having a smart load-balancer that knows when to “call in the big guns” and when a lightweight model is enough.
Optimize Prompts and Context Usage: Reducing token waste is an underrated cost saver. Long system prompts or unneeded file context can balloon token counts. Techniques like trimming prompt boilerplate, using tools (e.g. function calling or plugins) instead of pure text descriptions, and retrieving only relevant code snippets for the model to see can cut input length drastically. If using a large context model (like 1M-token Claude), be mindful that feeding the entire codebase every time costs a lot of input tokens – instead, use embeddings or search to pull just the parts needed for a given query. A well-engineered prompt strategy might cut your token usage by 30-50%, directly saving that portion of your budget.
In short, to stay within $600/month, combine multiple approaches: use fixed-cost plans (ChatGPT, Copilot) for interactive help, utilize open models on rented hardware for high-volume generation, and employ routing logic to dynamically assign each request to the lowest-cost model that can handle it. Many organizations also rotate subscriptions or providers as needed (“subscription swaps”) – for example, one month you might subscribe to Google’s Vertex AI trial to leverage a free Gemini quota, then the next month pause that and use Anthropic’s Claude credits, etc., aligning with project needs. Providers often offer free credits or discounts to encourage trials; savvy teams can sequence these opportunities to reduce out-of-pocket spend.
Multi-Model Routing Infrastructure (Meta-Routers)
The proliferation of LLM providers has given rise to meta-router systems – infrastructure that can route requests to different models or APIs based on criteria like query complexity, cost, or performance. These routing layers are becoming key for cost-aware and quality-optimized AI deployments. A well-designed router can automatically choose the best model per query, rather than statically using one model for all tasks. Below, we highlight some state-of-the-art routing solutions and projects:
OpenRouter Platform: In addition to being an aggregator, OpenRouter supports auto-routing policies. Developers can set preferences or fallback chains – e.g., “Try provider X’s model first, but if it’s a long code generation or fails tests, fall back to provider Y’s model.” OpenRouter’s enterprise features even allow routing based on data policies or regional rules. Crucially, it only bills for successful runs in a fallback scenario, so you aren’t double-charged when a query escalates. This built-in routing is relatively simple (rules-based), but it covers many use cases (like budget capping certain expensive models and diverting overflow to cheaper ones).
GPTRouter (Writesonic): GPTRouter is an open-source LLM API gateway that acts as a smart traffic director for AI models. It provides a unified API endpoint and can be configured to route requests to over 50 model endpoints (OpenAI, Anthropic, Cohere, Stability, Replicate, etc.). Its emphasis is on reliability and cost: it continuously health-checks models and will failover if one is down or slow. It also logs latency and token usage, enabling dynamic decisions – e.g., if GPT-4 is responding too slowly or nearing a cost threshold, GPTRouter could switch to a faster/cheaper model automatically. Because it’s open-source (GNU licensed) and free to deploy, companies can integrate it into their stack and customize the routing logic (for example, using a classifier to predict which model will best answer a given prompt). Some teams pair GPTRouter with monitoring tools to implement real-time cost-aware routing, ensuring no single provider’s bill blows up. Essentially, GPTRouter is a DIY solution to achieve what OpenRouter and others do as a service, with full control over how models are selected.
Martian LLM Router: Martian is a startup focusing on enterprise-grade dynamic model routing. Their router (backed by an Accenture investment) uses AI to predict which model will yield the best result for each query. It goes beyond simple rules by analyzing the content of the query and even the internals of model behaviors to decide routing. Martian’s system optimizes for cost, quality, and compliance – e.g., it might route a sensitive query only to an on-prem, approved model for compliance reasons, or choose a smaller model for a query if it predicts the larger model wouldn’t significantly outperform on that specific prompt. This kind of intelligent routing can dramatically lower average costs by not always using the most expensive model, without much loss in answer quality. Martian also highlights use in agentic workflows – in multi-step AI agents, their router picks the best model for each step (planning, coding, testing, etc.), reducing compounded errors in long chains.
OpenDevin: While primarily an open-source autonomous coding agent, OpenDevin functions as a meta-system that can integrate multiple LLMs. It is essentially an AI software engineer that can use tools (shell, browser, editor) and can be configured with different backend models. Through the litellm integration, OpenDevin lets you specify a primary model (say GPT-4 or Claude) but also could be extended to use specialized models for certain subtasks. For example, one could imagine OpenDevin using a coding-specific model for code generation and a math-specific model for analytic steps. The project’s mission is to “replicate and enhance” an AI developer agent named Devin, and it encourages community contributions to integrate new models and strategies. While not a general routing library, OpenDevin represents the agent-oriented approach to model routing: rather than a simple API proxy, it’s a full workflow that decides how to break down a software task and which AI (or tool) should handle each part. In doing so, it effectively routes subtasks to the most appropriate “specialist” model. This kind of meta-routing by task decomposition is an emerging area – for instance, an agent might use a fast model to generate many candidate solutions, then a strong model to evaluate or refine them, all behind the scenes.
Research Frameworks (RouteLLM, etc.): Academic and open research has also produced frameworks like RouteLLM, which formalizes the routing problem. RouteLLM provides algorithms to train a router model that directs queries between a big model and a small model to maximize a performance/cost objective. In tests, it achieved huge cost savings – e.g. using GPT-4 only ~14% of the time while still getting 95% of GPT-4’s quality on benchmarks (saving ~75% of token cost). While more experimental, such frameworks might be integrated into production in the near future, potentially as part of open-source toolkits (LangChain has primitive support for model selection chains, for example).
In summary, multi-provider routing has become an essential technique as of 2026. Teams aiming to optimize both cost and quality are increasingly adopting these meta-router solutions. Whether through a hosted service like OpenRouter or a self-hosted library like GPTRouter, the ability to “use the right model for each job” is the secret to squeezing maximum value out of LLMs. For a $600/month budget scenario, a well-tuned router could mean the difference between serving 1 million tokens of GPT-5 vs. 20 million tokens of mixed models for the same cost – a dramatic improvement in throughput. As the ecosystem evolves, expect routing to become even smarter (consider real-time bidding between model APIs, or community-driven router data that learns which models are best for which categories of queries). The end result is empowering developers to harness multiple AI models seamlessly: using fast ones when speed matters, cheap ones when cost matters, and powerful ones when quality matters – all within a unified workflow that keeps the project on budget and on target. Sources:
Vishwas Gopinath, “Best LLMs for coding in 2026,” Builder.io Tech Blog, Jan 28, 2026.
OpenRouter.ai – Programming Model Leaderboard, Feb 2026.
WhatLLM.org – Best Coding Models, Jan 2026, live benchmark rankings.
Fickle_Wall3932, “Claude Haiku 4.5 release info,” Reddit r/ClaudeCode, Oct 2025.
Noah Frank et al., AI Collective Newsletter, “Gemini 3… & MiniMax M2.5” (Feb 16, 2026).
Anthropic – Introducing Claude Haiku 4.5, Developer Blog (Oct 2025).
TrueFoundry – “Understanding Vercel AI Gateway Pricing,” (Feb 18, 2026).
OpenRouter Documentation – Pricing & FAQs.
Writesonic – GPTRouter Docs, (2025).
Sean Kerner, VentureBeat: “Model routing as key to enterprise AI” (Sept 17, 2024).
Isaac Ong et al., LMSYS RouteLLM Blog, July 1, 2024.
OpenDevin GitHub README, v0.1 (2025).

Sources

You said:
The models themselves ar not of concern as they'll rapidly change, how we'll scrape a given model's needed data to build our indices for Pareto and pareto\optimization alg + general arch is what simortant

ChatGPT said:

Thought for 9s
Yep — treat models as ephemeral. What matters is (1) how you continuously ingest/normalize “offer” data (pricing, limits, latency, reliability, quality signals), and (2) how your router turns that into hard-constraint filtering + Pareto/lexicographic selection without getting wrecked by missing/incorrect data.
Below is the architecture + scraping strategy that holds up even when models rotate weekly.

1. Key design principle: “Offer = routable unit”, not “model”
   A “model” name is marketing. Your router should operate on offers:
   Offer = (provider endpoint, model id, region, plan/quota regime, pricing, constraints, telemetry).

Same “model” across:

OpenRouter vs direct provider
different regions
different subscriptions/quotas
…is not the same offer. 2) Ingestion pipeline: adapters → canonical schema → derived metrics
2.1 Canonical schema (what you store)
You want 3 layers of fields:
A) Identity & capabilities (mostly static-ish)

provider, offerId, modelId
context window, max output, tool support, JSON mode, vision, etc.
B) Commercials & limits (changes often)
list prices (in/out, cache read/write)
rate limits / concurrency
plan entitlements / included usage / throttling rules
C) Observed telemetry (changes constantly)
p50/p95 latency, error rate, timeout rate
“format adherence” rate (JSON validity, tool-call success)
your per-role success metrics (tests pass, user re-asks, etc.)
2.2 Where to scrape each category
OpenRouter
They explicitly provide a Models API intended to expose “the most important information about all LLMs” as soon as confirmed.
You can also query your key status/credits via GET /api/v1/key.
Vercel AI Gateway
Has first-class Usage & Billing endpoints, including a generation lookup API that returns usage data, costs, and metadata for a request.
Pricing is “pay-as-you-go with no markups.”
Observability logs model usage/spend/metrics.
Direct providers
Usually: pricing pages, quotas, and rate-limits are in docs; actual usage is in billing dashboards or per-request usage metadata. (You’ll end up scraping + supplementing with your own metering.)
Self-host
You control everything: model weights metadata + hardware inventory + measured throughput.
Gateway-level tooling
LiteLLM Proxy is basically built for this: unified OpenAI-format API, cost tracking, routing strategies, logging.
If you don’t already have Helicone-style logging, LiteLLM can be your “data plane” fast. 3) The hard part: subscriptions and “blended $/mtok”
You need one universal function:
effectiveCost(offer, tokensIn, tokensOut, cacheStats, timestamp) -> dollars
To compute it reliably, model subscriptions as resource buckets with:
fixed monthly fee
included tokens (sometimes separate in/out, sometimes “messages”)
seasonal multipliers (2x, weekends, promos)
throttling regime after cap (latency penalty, hard block, or soft degrade)
swap/upgrade rules (mid-cycle changes)
Then compute marginal price plus a scarcity penalty:
Shadow price (turn subscription scarcity into per-call economics)
If a plan has “included” usage, you don’t want to blow it all on day 1.
Use:

remaining_ratio = remaining / expected_remaining (based on day-of-month)
shadow = k \* (1 / max(remaining_ratio, ε))
effective_unit_cost = marginal_unit_cost + shadow
That converts “quota scarcity” into a cost your router can optimize against. 4) Telemetry collection: don’t depend on vendors being consistent
You should treat provider-reported cost/usage as “nice-to-have” and still compute your own.
What to log per request (minimum)
request hash (for caching), offerId, role
tokens in/out (from response usage when available; else estimate)
wall-clock latency; streaming TTFT if possible
error classification (provider 5xx, rate limit, tool failure, schema failure)
cache hit/miss stats
Vercel AI Gateway supports retrieving generation usage/cost metadata (so you can backfill and reconcile). 5) Building your indices (Speed / Cost / Quality) from scraped + observed data
5.1 Speed index
Speed isn’t just latency. You explicitly care about conciseness (session time = turns × tokens × latency).
Predict:

latency*p95(offer, role)
expected_output_tokens(offer, role) (start with heuristics; later train)
optional: expected_turns(offer, role) from conversation logs
Then:
speed_cost = latency + α * output*tokens + β * turns
5.2 Cost index
cost_pred = effectiveCost(...) using shadow pricing and cache adjustments
include failure risk as expected cost:
cost_pred \*= 1/(success_prob) (or add penalty) so flaky endpoints get avoided
5.3 Quality index
Benchmarks change, vendors cherry-pick. You want a hybrid:
external scores (where available)
plus online outcome metrics you control:
test pass rate for coding
“needed escalation” rate (how often smaller model needed upgrade)
JSON/tool adherence
Net: quality_pred(role, offer) becomes a calibrated score. 6) Router algorithm (hard constraints → Pareto → final choice)
6.1 Hard constraints (must pass)
capabilities: tools/JSON/vision/context
max acceptable cost for this call (worst-case token cap)
max latency / p95 threshold
minimum quality threshold for role
compliance/data residency (if relevant)
6.2 Pareto set
Evaluate each surviving offer in objective vector:
minimize speed_cost
minimize cost_pred
maximize quality_pred (or minimize -quality)
Compute non-dominated offers.
6.3 “Optimize in order after all are met”
If your policy is lexicographic:
pick offers within ε of best quality
among them pick cheapest within ε
among them pick fastest
This gives stable behavior and avoids weird flips.
6.4 Reliability fallback chain
Even if you pick one offer, you need a fallback order:
next best in the Pareto set
then “safe” fallback (high adherence model) if schema/tooling failed
and circuit-break providers that are erroring (LiteLLM supports routing strategies and rate-limit-aware routing patterns)
OpenRouter itself does provider/GPU fallback when it sees 5xx or rate-limit.
Still: you want your own fallback logic because you’re optimizing your own objectives. 7) Research-backed direction for “advanced later”
If/when you go beyond rules/Pareto:
Preference-aligned routing (learn router from preference data / outcomes) is now a well-trodden approach (RouteLLM, etc.).
Jan 2026 introduced LLMRouterBench explicitly framing routing as performance–cost–latency Pareto optimization and benchmarking routers in that space.
Translation: your Pareto-first design is aligned with the state of the art, and you can later swap the scoring/prediction parts for learned routers without rewriting the system. 8) Concrete architecture that won’t collapse
Data plane
Single gateway for all calls (pick one):
LiteLLM Proxy if you want OSS + deep spend/routing knobs
or your own thin gateway if you already have Vercel AI Gateway + OpenRouter
Control plane (the brain)
Offer Registry (canonical offers + capabilities)
Commercial Engine (plans → effectiveCost + shadow pricing)
Telemetry Store (latency/errors/format adherence)
Quality Store (benchmarks + online eval results)
Router Service (hot path)
Slow loop (hourly/daily)
refresh provider metadata (OpenRouter models API, Vercel usage endpoints, provider docs)
update quota + shadow prices
retrain/update predictors (tokens, latency, success prob) 9) Budget $600/month: how it affects the design
Budget doesn’t change the router logic — it changes control plane constraints:
allocate monthly “role budgets” (doc_writer, coding_agent, fast_chat)
enforce per-call caps (worst-case token estimate × effectiveCost)
shadow pricing becomes more aggressive as you approach burn limits
if you exceed a daily budget, router flips to “degraded mode” (cheap/self-host offers only)
If you want, I’ll write you a canonical schema (JSON/YAML) + the exact ingestion adapters you need for:
OpenRouter models + key status endpoints
Vercel AI Gateway generation lookup + usage
LiteLLM spend tracking + router strategies
…and the Pareto router function that consumes those tables and outputs offerId + fallbackChain.

You said:
I want a PRD \ ALD w\ ascii diagram

ChatGPT said:
Good. We’ll design this like a real system, not a hacky router script.
You’re building:

A cost-aware, speed-aware, quality-aware multi-provider LLM routing control plane
with dynamic subscription economics + Pareto / lexicographic optimization.
Below is a combined PRD + ALD, followed by ASCII architecture diagrams.
📘 PRODUCT REQUIREMENTS DOCUMENT (PRD)

1.  Product Name
    Helios Router (placeholder)
2.  Problem Statement
    LLM providers, pricing, and performance characteristics change rapidly.
    Hardcoding model choices leads to:
    Cost explosions
    Latency unpredictability
    Quality regressions
    Subscription under/over-utilization
    We need a:
    Model-agnostic routing system that continuously ingests provider data,
    computes dynamic economics,
    and selects offers using hard constraints + Pareto optimization.
3.  Core Objectives
    3.1 Functional Objectives
    Ingest provider metadata (pricing, limits, capabilities).
    Ingest subscription/plan state dynamically.
    Track live telemetry (latency, errors, token usage, quality signals).
    Compute:
    Effective cost per request
    Speed index
    Quality index
    Apply:
    Hard constraint filtering
    Pareto frontier pruning
    Lexicographic final selection
    Support fallback chains.
    Enforce monthly $600 budget.
    Allow role-specific policies (coding, doc writer, fast chat, etc).
4.  Non-Functional Requirements
    Category Requirement
    Latency Router decision < 5ms p95
    Reliability No single provider dependency
    Observability Full per-offer telemetry
    Extensibility New provider adapter < 1 day integration
    Budget Control Hard stop + degraded mode
    Determinism Same input state → same selection
5.  Pillars (Optimization Axes)
    5.1 Speed
    Includes:
    p95 latency
    expected output tokens
    expected turns
    Speed Score:
    speed*score = latency_ms + α * expected*output_tokens + β * expected_turns
    5.2 Cost
    Cost includes:
    input tokens
    output tokens
    cache adjustments
    subscription shadow price
    Effective cost:
    effective_cost = marginal_cost + shadow_price
    Shadow price increases as quota is consumed.
    5.3 Quality
    Quality index derived from:
    External benchmarks
    Online evaluation
    Format adherence
    Test pass rate (for coding roles)
    quality_score(role, offer)
6.  Hard Constraints
    Before optimization, offers must satisfy:
    Capability requirements (tools, JSON, vision)
    Context length
    Maximum cost threshold
    Latency threshold (optional)
    Minimum quality threshold
    Compliance rules (if needed)
7.  Selection Strategy
    Step 1 — Filter by hard constraints
    Step 2 — Compute objective vector:
    O = (
    minimize speed_score,
    minimize effective_cost,
    maximize quality_score
    )
    Step 3 — Compute Pareto frontier
    Step 4 — Apply lexicographic tie-break:
    Example order:
    Highest quality
    Lowest cost
    Lowest speed score
8.  Budget Strategy ($600/month)
    8.1 Monthly Control Plane
    Role-level budget allocation
    Shadow pricing updated daily
    Degraded mode after 85% budget consumption
    8.2 Degraded Mode
    Disable premium offers
    Use:
    self-host
    mid-tier
    cached responses
9.  Roles
    Example roles:
    fast_chat
    doc_writer
    code_simple
    code_complex
    agentic_workflow
    eval_model
    Each role defines:
    hard constraints
    optimization order
    quality threshold
    token prediction multiplier
    📐 ARCHITECTURAL LOW LEVEL DESIGN (ALD)
10. System Overview
    ┌─────────────────────┐
    │ Client Request │
    │ (role + prompt) │
    └─────────┬───────────┘
    │
    ▼
    ┌────────────────┐
    │ Router API │
    │ (Hot Path) │
    └───────┬────────┘
    │
    ┌─────────────┼─────────────┐
    ▼ ▼ ▼
    Hard Constraint Objective Calc Fallback Logic
    Filter (Speed/Cost/Quality)
    │
    ▼
    Pareto Frontier
    │
    ▼
    Lexicographic Select
    │
    ▼
    Offer Execution
    │
    ▼
    Telemetry Logging
11. Control Plane vs Data Plane
    ┌────────────────────────────┐
    │ CONTROL PLANE │
    ├────────────────────────────┤
    │ Offer Registry │
    │ Subscription Engine │
    │ Shadow Pricing Engine │
    │ Quality Index Engine │
    │ Telemetry Aggregator │
    │ Budget Allocator │
    └──────────────┬─────────────┘
    │
    ▼
    ┌────────────────────────────┐
    │ DATA PLANE │
    ├────────────────────────────┤
    │ Router (hot path) │
    │ Provider Adapters │
    │ Execution Gateway │
    └────────────────────────────┘
12. Provider Adapter Layer
    Each provider adapter must implement:
    interface ProviderAdapter {
    fetchModels()
    fetchPricing()
    fetchUsage()
    executeRequest()
    parseUsageFromResponse()
    }
    Adapters:
    OpenRouter Adapter
    Vercel AI Gateway Adapter
    Direct Provider Adapter
    Self-host Adapter
13. Offer Registry Schema
    Canonical Offer Object:
    Offer {
    offerId
    provider
    modelId
    region

        capabilities {
            tools
            json_mode
            vision
            max_context
        }

        pricing {
            input_per_million
            output_per_million
            cache_read_per_million
        }

        limits {
            rpm
            tpm
            concurrency
        }

        telemetry {
            latency_p50
            latency_p95
            error_rate
            format_adherence
        }

        quality_scores {
            per_role_score
        }

        shadow_price

    }

14. Shadow Pricing Engine
    remaining_ratio = remaining_quota / expected_remaining_quota

shadow_price = k \* (1 / max(remaining_ratio, ε))
As quota decreases → effective cost increases. 6. Pareto Computation
Given N offers:
for offer in offers:
compute (speed, cost, -quality)

remove dominated offers

ParetoSet = non-dominated offers
Dominated if:
A dominates B if:
A.speed <= B.speed
A.cost <= B.cost
A.quality >= B.quality
AND at least one strictly better 7. Fallback Strategy
Primary: Best Pareto offer
Secondary: Next Pareto offer
Tertiary: High-adherence safe model
Quaternary: Cheapest self-host
Circuit breaker:
Disable offer after X failures
Auto-recover after cooldown 8. Slow Loop Jobs
Hourly:
Update usage from providers
Update shadow pricing
Daily:
Recompute quality indices
Recompute budget burn projections
Monthly:
Plan swap decision
Subscription optimization
🔬 Future Extensions (V2+)
Learned routing model (RouteLLM style)
Reinforcement learning for role-based routing
Predictive token estimator model
Multi-step agent-aware routing
Confidence-based early exit
🧠 Design Philosophy
Models are commodities.
Offers are economic units.
Subscriptions are resource pools.
Routing is a constrained multi-objective optimization problem.
Pareto-first avoids premature scalar weighting mistakes.
Lexicographic tie-break gives stability.
If you'd like next:
I can generate the database schema
Or the exact hot-path routing pseudocode
Or the control-plane microservice breakdown
Or a budget simulation model for $600/month
What layer do you want to go deeper on?

You said:
Need user journeys \ api processes\pileiens etc

ChatGPT said:
Alright—below are user journeys, API processes, and pipelines for the router system. This is written as a PRD/ALD extension: concrete flows, endpoints, and event pipelines.
User Journeys
Journey A — “Route a request” (hot path)
Actor: your app / agent / IDE extension
Goal: pick best offer under constraints, execute, log, and fallback if needed.
Client sends request with role, hardConstraints, prompt/messages, and optional budgets.
Router loads latest snapshot of:
offers + capabilities
pricing + shadow prices
telemetry + predicted latency
quality indices per role
Router filters hard constraints.
Router computes objective vectors, Pareto frontier, lexicographic pick.
Router executes call via gateway/provider adapter.
Router logs telemetry + usage and returns response + route metadata.
If call fails, router executes fallback chain until success or terminal failure.
Outputs: response, routeTrace, offerId, fallbackUsed?, cost estimate, usage tokens, latency stats.
Journey B — “Add a new provider”
Actor: you (admin/devops)
Goal: integrate a new provider with minimal effort.
Implement adapter interface (metadata + usage + execution).
Register adapter + credentials in secrets manager.
Run “adapter validation” job:
list models
fetch pricing
execute test request
Provider offers appear in Offer Registry with state=inactive.
Enable provider for limited roles / canary percent.
Observe telemetry; gradually expand.
Journey C — “Subscription changes mid-month”
Actor: system + you
Goal: keep effective costs accurate and prevent quota blowups.
Subscription adapter scrapes usage/quota/renewal date.
Commercial Engine recomputes:
remaining quotas
throttling risk
shadow prices
Budget allocator may:
tighten per-role caps
enable cheaper offers
enter degraded mode if nearing burn limit
Journey D — “Degraded mode after budget burn”
Actor: system
Goal: keep service alive within budget.
Budget burn crosses threshold (e.g. 85% of monthly).
Router policy flips:
disables premium offers
forces cache-first behavior
prioritizes self-host / low-cost API models
User receives responses with “degraded mode” metadata.
Core API Processes

1. Public Router API (hot path)
   POST /v1/route
   Routes + executes (one stop).
   Request

{
"role": "code*complex",
"messages": [...],
"hard": {
"maxCostUsd": 0.12,
"maxLatencyMsP95": 2500,
"minQuality": 0.78,
"needsTools": true,
"needsJson": false,
"minContextTokens": 32000
},
"soft": {
"optOrder": ["quality", "cost", "speed"],
"epsilon": { "quality": 0.02, "cost": 0.10, "speed": 0.15 }
},
"meta": {
"projectId": "atoms",
"userId": "u_123",
"traceId": "t*..."
}
}
Response
{
"response": {...},
"routeTrace": {
"selectedOfferId": "openrouter:anthropic:claude-opus:us-east",
"paretoSet": ["...","..."],
"fallbackChain": ["...","..."],
"fallbackUsed": false,
"scores": {
"speedScore": 1880,
"costUsd": 0.083,
"qualityScore": 0.84
}
},
"usage": {
"promptTokens": 12450,
"completionTokens": 2800,
"totalTokens": 15250
}
}
POST /v1/plan
Dry-run: returns route decision only (no execution). Used for debugging, testing, CI. 2) Admin APIs
POST /v1/admin/providers/:providerId/enable
Enable provider offers (optionally scoped by roles).
POST /v1/admin/offers/:offerId/state
Set active|inactive|canary|blocked.
POST /v1/admin/policies
Update role policies (constraints + opt order).
GET /v1/admin/health
Shows provider health, error rates, disabled offers, budget burn.
Pipelines (Data + Control Plane)
You want three pipelines:
Offer/Metadata pipeline (capabilities/pricing/limits)
Telemetry pipeline (latency/errors/usage/format adherence)
Economics pipeline (subscriptions → quotas → shadow prices → budgets)
Pipeline 1 — Offer & Metadata Ingestion
Goal: keep offer registry accurate.
Inputs

OpenRouter models/pricing API
Vercel AI Gateway model mappings (if used)
Direct provider docs/APIs
Self-host registry (your inference fleet inventory)
Stages
Fetch raw model lists and pricing
Normalize to canonical Offer
Deduplicate and assign stable offerId
Validate capabilities via probe calls (optional)
Write to Offer Registry + version snapshot
ASCII
[Provider APIs] [Docs/HTML] [Self-host Fleet]
| | |
+-------> [Adapters / Scrapers] <---+
|
v
[Normalizer + Validator]
|
v
[Offer Registry (db)]
|
v
[Offer Snapshot (immutable)]
Pipeline 2 — Telemetry & Observability
Goal: build speed/reliability predictors and online quality stats.
Inputs

Router execution traces
Gateway logs (Vercel, LiteLLM, OpenRouter metadata)
Local inference metrics (vLLM, TGI, etc.)
Stages
Log per-request metrics:
latency (TTFT, total)
tokens in/out
cache hit/miss
errors + retries
output schema validity
Aggregate into rolling windows (5m, 1h, 24h):
p50/p95
error rate
adherence rate
Publish “Telemetry Snapshot” used by router hot path.
ASCII
[Router Calls]
|
v
[Event Log / Queue] ---> [Stream Aggregator] ---> [Telemetry DB]
|
v
[Telemetry Snapshot]
|
v
(Hot Path)
Pipeline 3 — Economics: Subscriptions, Budgets, Shadow Prices
Goal: convert messy subscription rules into effective marginal cost.
Inputs

Subscription dashboards (scraped)
Provider billing usage endpoints (when available)
Your metering (truth source)
Seasonal multipliers + promos
Manual overrides (“freeze spending on provider X”)
Stages
Scrape/ingest current plan status:
remaining quota
renewal date
throttle regime
Compute:
remaining_ratio vs expected_remaining (time-based)
shadow price per plan/model
Produce effectiveUnitCost function parameters per offer.
Budget allocator:
sets role budgets and per-day burn caps
triggers degraded mode flags
ASCII
[Sub Dashboards] [Billing APIs] [Your Metering]
| | |
+-------> [Plan Adapters / Scrapers]
|
v
[Commercial Engine]
(quota, multipliers, throttle, shadow)
|
v
[Effective Cost Table + Budgets]
|
v
(Hot Path)
How the Router Uses Pipelines (Hot Path Data Model)
The router should run purely off snapshots to stay fast and deterministic:
OfferSnapshot (capabilities + base pricing)
TelemetrySnapshot (latency/errors/adherence)
EconomicsSnapshot (effective cost + shadow price + budget state)
QualitySnapshot (per-role quality indices)
ASCII
┌────────────────────────┐
Request + Role ---> │ Router Hot Path │
│ loads snapshots: │
│ - OfferSnapshot │
│ - TelemetrySnapshot │
│ - EconomicsSnapshot │
│ - QualitySnapshot │
└───────────┬────────────┘
v
Hard Filters -> Pareto -> LexiPick -> Execute -> Log
Execution + Fallback Process
Failure types matter (because fallback choices differ):
Rate limit / quota → switch provider/offer immediately
Timeout → switch to faster offer
Schema/tool failure → switch to “high adherence” offer
Bad output quality (detected by tests) → escalate quality tier
Fallback chain generator
Next best on Pareto frontier
Same provider, different region (if helpful)
Different provider, same “tier”
Safe high-adherence model
Cheapest survivable fallback (self-host)
Optional: “Plan-only router” for agent frameworks
For complex agents you may want:
route each step differently (planner vs coder vs reviewer)
or run N candidates cheap then validate with strong model
Provide:
POST /v1/route/planOnly
POST /v1/route/executeSelected
This helps when you want external orchestrators (Cursor/Codex-like) to control multi-step flows.
Deliverables Checklist (what you’d ship)
Canonical Offer schema + snapshots
Adapter interfaces + initial adapters (OpenRouter, Vercel, self-host)
Telemetry event schema + aggregator
Subscription plan schema + shadow pricing engine
Router service (hard filters + pareto + lexi + fallback)
Admin policy editor (roles + budgets)
Dashboards: spend, latency, routing decisions, failovers
If you want the next level, tell me which runtime you’re building this in (Go vs TS vs Python). I’ll output:
exact OpenAPI spec
event schemas
storage tables
and the “snapshot loading + pareto router” pseudocode in that language.

You said:
Walk me through each indice, how its calculated, how model\provider addtions would work, how the budget is moved around etc

ChatGPT said:
Good. Now we’re going to treat this like an actual quantitative system.
No hand-waving. Just math + mechanics.

You have three indices:

Speed
Cost
Quality
And then a Budget Control Layer that modulates cost via shadow pricing.
I’ll walk through:

Exactly how each index is calculated
How new models/providers slot in
How budget is dynamically redistributed
How it all interacts in the Pareto engine
PART 1 — SPEED INDEX
Speed is not just latency.
For coding workloads, speed = time to usable answer, which includes:

TTFT (time to first token)
Total latency
Output length (longer outputs = longer read + parse + post-process)
Expected turns (agent workflows)
1.1 Raw Observables
Collected per offer:
latency_p50
latency_p95
ttft_p50
tokens_per_second
error_rate
Also per role:
expected_output_tokens(role, offer)
expected_turns(role)
1.2 Speed Formula
For each request, predict:
predicted_latency = latency_p95(offer)

predicted_generation_time =
expected_output_tokens / tokens_per_second

session_time =
predicted_latency

- predicted_generation_time
- gamma \* expected_turns
  Where:
  gamma = penalty per turn (e.g., 300ms–1000ms depending on workflow)
  1.3 Normalized Speed Score
  To compare across offers:
  speed_score =
  session_time / median_session_time_across_offers
  Lower is better.
  This avoids overweighting raw milliseconds.

  1.4 Why Not Just Use Latency?
  Because:
  Claude Opus may be slow but concise.
  Gemini Flash may be fast but verbose.

If verbose models increase output tokens by 40%, they are slower in real usage.

So speed must include verbosity.

PART 2 — COST INDEX
This is the most complex.
Cost must reflect:

Raw token pricing
Cache adjustments
Subscription quotas
Throttling penalties
Shadow pricing
Failure retries
2.1 Base Marginal Cost
base_cost =
(input_tokens \* input_price_per_token)

- (output*tokens * output*price_per_token)
  2.2 Cache Adjustment
  If cache hit ratio is known:
  effective_input_tokens =
  input_tokens * (1 - cache_hit_rate)

effective_cost = recompute using adjusted tokens
2.3 Retry Risk Adjustment
If error_rate = 5%:
Expected retries = 1 / (1 - error_rate)

cost_adjusted =
effective_cost \* (1 / (1 - error_rate))
This penalizes flaky providers automatically.
2.4 Subscription Shadow Pricing
Now the critical part.
If you have included usage, marginal cost is artificially low.

To avoid front-loading usage:

remaining_ratio =
remaining_quota / expected_remaining_quota_today

shadow_multiplier =
1 / max(remaining_ratio, epsilon)

shadow_cost =
base_cost \* shadow_multiplier
As quota depletes:
remaining_ratio drops
multiplier increases
model becomes "more expensive"
This smoothly pushes router away from draining quota.
2.5 Final Cost Index
cost_score = shadow_cost / median_cost_across_offers
Lower is better.
PART 3 — QUALITY INDEX
Quality must be:
Role-specific
Dynamic
Measured from your usage
3.1 External Baseline
Normalize benchmark scores:
normalized_benchmark =
(model_score - min_score) / (max_score - min_score)
3.2 Online Performance Signals
Per role track:
For coding:

test_pass_rate
required_escalation_rate
syntax_validity_rate
tool_success_rate
Example composite:
quality_score =
w1 \* normalized_benchmark

- w2 \* test_pass_rate
- w3 \* (1 - escalation_rate)
- w4 _ format_adherence
  All normalized 0–1.
  3.3 Confidence Adjustment
  If offer has low sample size:
  quality_score_adjusted =
  quality_score _ sqrt(sample_count / threshold)
  Prevents new models from being overtrusted early.
  PART 4 — PARETO ENGINE
  Now each offer has:
  (speed_score, cost_score, quality_score)
  Pareto keeps all non-dominated offers.
  An offer A dominates B if:

speed_A <= speed_B
cost_A <= cost_B
quality_A >= quality_B
at least one strictly better
Pareto frontier typically ends up 2–5 offers.
PART 5 — BUDGET ENGINE
Now the real question:
How does budget move around?
5.1 Monthly Budget Model
Total monthly budget = $600
Split into:

fixed subscriptions (Copilot, Claude UI, etc.)
API budget pool
self-host infra budget
Example:
$200 subscriptions
$300 API pool
$100 GPU hosting
5.2 Daily Burn Tracker
Each day:
expected_daily_burn =
remaining_budget / days_remaining
If actual burn > expected:
increase global shadow multiplier
restrict premium roles
5.3 Role-Level Budget Allocation
Example:
code_complex → 40%
doc_writer → 20%
fast_chat → 15%
agent_workflow → 25%
Each role has:
remaining_role_budget
Shadow pricing also applied at role level.
If code_complex overspends:

its shadow multiplier increases
router shifts to mid-tier offers
or enforces stricter cost caps
5.4 Budget Rebalancing
Nightly job:
If some roles underspent:

redistribute surplus proportionally
If high-quality model underused:
reduce its shadow slightly.

If model too popular:

increase shadow.

PART 6 — ADDING A NEW MODEL / PROVIDER
Here’s the lifecycle.
6.1 Adapter Adds Offer
Adapter fetches metadata
Canonical Offer created
State = "canary"
6.2 Canary Phase
Only 5–10% of traffic
Collect telemetry
Collect quality stats
6.3 Scoring Initialization
Initial:
cost known
speed estimated from first 100 calls
quality = benchmark-weighted baseline
After enough data:
quality replaced by live metrics
6.4 Automatic Integration
Once confidence threshold met:
state → active
participates fully in Pareto
No hardcoded changes required.
PART 7 — HOW EVERYTHING INTERACTS
ASCII Overview:
┌────────────────────┐
│ Request + Role │
└─────────┬──────────┘
▼
┌──────────────────────┐
│ Load Snapshots │
│ Speed/Cost/Quality │
└─────────┬────────────┘
▼
Hard Constraint Filter
▼
Compute Indices
▼
Pareto Frontier
▼
Lexicographic Pick
▼
Execute
▼
Log Metrics
▼
Telemetry + Economics Update
PART 8 — WHY THIS WORKS LONG TERM
Because:
Models are ephemeral.
Indices are stable abstractions.
Budget modulation happens via shadow pricing.
Pareto avoids premature scalar weighting.
New providers plug into canonical schema.
If you want next:
I can:

Simulate a $600 month with real numbers
Show how shadow pricing evolves over 30 days
Or design the learned-router V2 upgrade path (bandits / preference learning)
Where do you want to push this deeper?

You said:
Show me example model \ provider catalog, and how we route to a model, and from there to a provider (or perhaps model\provider pairs to sink in cost from the get go?)

ChatGPT said:
You want model/provider pairs from day 1. Treat “model” as a label; routing should pick an Offer (provider+model+region+plan). That’s how you bake cost/limits/subscriptions into the decision before you execute.
Below: (1) an example catalog, (2) how routing works, (3) how execution maps to provider, (4) why “Offer-first” beats two-stage model→provider in practice.

1. Example Catalog (Offer-first)
   Think of the catalog as two layers:
   ModelSpec: capability facts (context, tools, modalities)
   Offer: a routable endpoint for a model via a provider, with pricing + limits + plan linkage
   1.1 models.yaml (capabilities / stable-ish)
   models:

- modelId: claude-opus
  family: claude
  capabilities:
  tools: true
  jsonMode: true
  vision: false
  maxContextTokens: 1000000
  maxOutputTokens: 8192

- modelId: gemini-flash
  family: gemini
  capabilities:
  tools: true
  jsonMode: true
  vision: true
  maxContextTokens: 1048576
  maxOutputTokens: 8192

- modelId: qwen-coder-32b
  family: qwen
  capabilities:
  tools: false
  jsonMode: false
  vision: false
  maxContextTokens: 65536
  maxOutputTokens: 8192
  1.2 plans.yaml (subscriptions / quotas / shadow pricing inputs)
  plans:
- planId: openrouter-payg
  type: payg
  provider: openrouter
  monthlyFeeUsd: 0
  includedTokens: null
  throttle: none

- planId: google-vertex-sub
  type: subscription
  provider: google
  monthlyFeeUsd: 200
  included:
  gemini-flash:
  inputTokens: 200000000
  outputTokens: 50000000
  seasonalMultipliers:
  - name: winter_promo
    starts: 2026-02-01
    ends: 2026-02-28
    multiplier: 2.0

- planId: selfhost-gpu-rentals
  type: infra
  provider: selfhost
  monthlyFeeUsd: 120
  includedTokens: null
  throttle: none
  1.3 offers.yaml (the thing you actually route to)
  Each offer references a modelId and a planId.
  offers:

# Same modelId, different offers (provider+region+plan) => different economics.

- offerId: openrouter:claude-opus:us-east
  modelId: claude-opus
  provider: openrouter
  endpoint: https://openrouter.ai/api/v1/chat/completions
  region: us-east
  planId: openrouter-payg
  pricing:
  inputPerMTokUsd: 5.00
  outputPerMTokUsd: 25.00
  cacheReadPerMTokUsd: 0.50
  cacheWritePerMTokUsd: 6.00
  limits:
  rpm: 600
  tpm: 600000
  concurrency: 50

- offerId: direct-anthropic:claude-opus:us-west
  modelId: claude-opus
  provider: anthropic
  endpoint: https://api.anthropic.com/v1/messages
  region: us-west
  planId: openrouter-payg
  pricing:
  inputPerMTokUsd: 5.00
  outputPerMTokUsd: 25.00
  cacheReadPerMTokUsd: 0.50
  cacheWritePerMTokUsd: 6.00
  limits:
  rpm: 200
  tpm: 200000
  concurrency: 20

- offerId: google:gemini-flash:us-central
  modelId: gemini-flash
  provider: google
  endpoint: https://vertexai.googleapis.com/v1/projects/.../locations/us-central1/publishers/google/models/gemini-flash:generateContent
  region: us-central
  planId: google-vertex-sub
  pricing:
  inputPerMTokUsd: 0.50
  outputPerMTokUsd: 3.00
  cacheReadPerMTokUsd: 0.10
  cacheWritePerMTokUsd: 0.60
  limits:
  rpm: 1000
  tpm: 2000000
  concurrency: 200

- offerId: selfhost:qwen-coder-32b:phoenix
  modelId: qwen-coder-32b
  provider: selfhost
  endpoint: http://10.0.0.12:8000/v1/chat/completions
  region: phoenix
  planId: selfhost-gpu-rentals
  pricing: # For self-host you can store “effective” $/MTok derived from GPU-hour math.
  inputPerMTokUsd: 0.15
  outputPerMTokUsd: 0.35
  cacheReadPerMTokUsd: 0.00
  cacheWritePerMTokUsd: 0.00
  limits:
  rpm: 9999
  tpm: 9999999
  concurrency: 8
  Important: you can still keep “modelId” as a label, but you route to offerId.

2. How we route (Offer-first)
   2.1 Input to router
   {
   "role": "code_complex",
   "hard": {
   "needsTools": true,
   "minContextTokens": 32000,
   "maxCostUsd": 0.12,
   "maxLatencyMsP95": 2500,
   "minQuality": 0.80
   },
   "messages": [...],
   "tokenEstimate": { "in": 12000, "out": 2500 }
   }
   2.2 Router loads snapshots
   OfferSnapshot (offers + capabilities + base pricing)
   TelemetrySnapshot (latency/error/adherence)
   EconomicsSnapshot (quota remaining + shadow multipliers)
   QualitySnapshot (role→offer quality score)
   2.3 Hard-filter (capabilities, context, etc.)
   Example: selfhost:qwen-coder-32b has tools=false so it gets filtered out for needsTools=true.
   Remaining offers might be:

openrouter:claude-opus:us-east
direct-anthropic:claude-opus:us-west
google:gemini-flash:us-central
2.4 Compute indices per offer
Cost (effective) for google:gemini-flash
Base:
in: 12000 tokens, out: 2500 tokens
input cost: 0.50 / 1,000,000 = 0.0000005 per token
output cost: 3.00 / 1,000,000 = 0.000003 per token
base = 12000*0.0000005 + 2500*0.000003
= 0.006 + 0.0075
= $0.0135
Now apply subscription shadow multiplier, say 1.6 (quota running low):
effective_cost = 0.0135 \* 1.6 = $0.0216
Speed
Use telemetry p95 latency + predicted generation time.
Quality
Use role-weighted score.
2.5 Pareto prune + lexicographic pick
You pick offerId, and generate fallback chain.
Result:

Primary: openrouter:claude-opus:us-east (higher quality, still within cost cap)
Secondary: google:gemini-flash:us-central (cheap + fast)
Tertiary: direct-anthropic:claude-opus:us-west (if OpenRouter fails) 3) Executing: offerId → provider adapter
Execution is simple once you route to offers.
3.1 Adapter mapping
If offer.provider == openrouter → OpenRouterAdapter
If offer.provider == google → VertexAdapter
If offer.provider == selfhost → OpenAICompatAdapter (vLLM/TGI)
If offer.provider == anthropic → AnthropicAdapter
Offer contains the endpoint and any provider-specific params, so execution is deterministic. 4) Should it be model→provider two-stage?
You can, but it’s usually worse.
Two-stage (model → provider)
Pros:
conceptually clean
Cons:
you select “claude-opus” without considering:
provider-specific rate limits
provider outages
subscription quotas
region latency differences
different caching prices
So you end up doing offer-routing anyway as a second step.
Offer-first (model+provider pair)
Pros:
economics and limits baked in from the start
consistent scoring
correct handling of subscriptions/quotas/outages
easy fallback across providers
Cons:
bigger catalog (fine; it’s what you actually need)
Recommendation: Offer-first, always. 5) What “routing to a model” means in this architecture
You don’t route to a model. You route to an offer, and optionally record modelId for analytics.
In logs you store both:

offerId (what executed)
modelId (what category it belonged to)
That lets you say:
“We used claude-opus 2,000 times”
“But 80% via OpenRouter, 20% direct” 6) Fallback chain example (generated, not hand-written)
You generate fallback based on why primary fails:
Timeout → pick next fastest offer on Pareto set
Rate limit/quota → pick different provider or region
Tool/schema failure → pick highest adherence offer
Example fallback chain:
[openrouter:claude-opus:us-east]
-> if 429: [google:gemini-flash:us-central]
-> if schema fail: [direct-anthropic:claude-opus:us-west]
-> if all fail: [selfhost:qwen-coder-32b:phoenix] (if tools not required)
If you want, next I’ll output:
a complete canonical JSON schema for Offer/Plan/Telemetry/Quality snapshots
the routing pseudocode (hard filter → pareto → lexi → fallback)
and a catalog expansion rule (how one “model” becomes 6–20 offers across providers/regions/plans).

You said:
Here's a couple ground truths to assist:

I pay for:

200$ \ mo Claude Max: Calculates to ~3b Tok a mo (but dynamic usage and across 3 different models, so unclear how it stabilizes and works out, but we take this as a baseline, also this incas cached tokens)

200$ \ mo Codex (same as above notes) 11b Tok a mo

200$ \ mo Cursor ~ 600$ of usage lets assume at cost

40$ \ mo Minimax (300 prompts every 5 hours)

Copilot Student Pro for free

GLM Max 80$ Plan

Gemini \ Antigravity Free plans via google AI premium 20\mo

Kilo Code, Roo Code, Opencode Zen, Openrouter, kimi qwen, (these are that im aware of ) have promotional, exclusive, or free seasonal \ preview models, so I can't list what models but we would evaluate at this times and include in our systems, roo\kilo\opencode are harnesses whose api we use in our own modified codex cli harness.

Of all of these currently:

Gemini 3 pro, 3 flash
GLM-5, 5-code
Claude 4.6 Sonnet, OPus, 4.5 Haiku
GPT 5.3 Coex (med+) 5.3 codex spark (med+)
Minimax m2.5
Kimi k2.5
Deepseek v3.2
qwen3.5 variants
Ne models

Gpt 4.1, gpt 5 mini offered as 0x usage via copilot (!!!) this is one of the only true unlimited use models we have

All of the above we have a program already that can authenticate and map oa. Proper api for our codex harness to consume, so we view them as equal to the same as an oepnAI compatible provider.

Blended costs for each would need to be calculated, speed calculated and trained based one eality (perhaps the same for costs\conciseness?)

Quality to train is a big ask, here simply we will again rely on you asking me to provide a set of benchmark values that I grab manually (most are in release pages in images, no way for you to get), but we must expect that it will be spotty, e.g. model A has 5 of 8, model b 6 of 8 but the 2 missing are part of A's 5 etc, so we must be able to still form a stable index here

ChatGPT said:
Perfect—those ground truths are enough to lock the design.
You already have an OpenAI-compatible abstraction for execution, so the only hard part is: turning messy plan economics + spotty quality data into stable per-offer indices.

Below is exactly how I’d model:

the catalog given your subscriptions
blended cost per offer (including “unlimited” Copilot)
speed/conciseness training
quality index with missing benchmarks that doesn’t collapse
how offers participate in Pareto routing

1. Catalog: what you route to (Offer-first)
   You should represent everything as Offer = (provider endpoint + modelId + plan).
   Even if many are “OpenAI-compatible”, they’re different offers because their economics differ.

Example offer IDs in your world:

claude-ui:max:sonnet-4.6
claude-ui:max:opus-4.6
openai:codex-sub:gpt-5.3-codex-medplus
openai:codex-sub:gpt-5.3-codex-spark-medplus
cursor:sub:whatever-model (Cursor has its own internal routing; treat Cursor as an offer with a blended unit cost)
copilot:student:openai-gpt-5-mini (unlimited)
copilot:student:openai-gpt-4.1 (unlimited)
glm:max:glm-5-code
google:premium:gemini-3-pro
google:premium:gemini-3-flash
minimax:sub:m2.5
openrouter:payg:deepseek-v3.2
promo:harness:kilo|roo|opencode:<rotating> (these are offers whose identity changes often)
Key point: Cursor/Copilot/Claude UI/Codex sub are offers even if you can call them via an OpenAI-style shim. The plan is the asset. 2) Cost Index: blended unit cost per plan → per-offer marginal cost
You want this function for routing:
effectiveCostUsd(offer, tokensIn, tokensOut, cacheHit, t)
The clean way: for each plan, compute an Effective Unit Cost (EUC) in $/token (or $/MTok). Then cost per call is EUC × tokens.
2.1 Plan types (you have all of these)
A) Pay-as-you-go
Easy:
EUC_in = price_in_per_token
EUC_out = price_out_per_token
B) Fixed-fee “token bucket” (your Claude Max / Codex sub claims)
You gave:
Claude Max: $200/mo ≈ 3B tokens/mo (includes cached tokens)
Codex sub: $200/mo ≈ 11B tokens/mo
Cursor: $200/mo ≈ $600 usage equivalent
Model it as:
EUC_blended = monthly_fee / expected_tokens_covered
So baseline:
Claude Max: 200 / 3,000,000,000 = $0.0000000667/token = $0.0667/MTok
Codex sub: 200 / 11,000,000,000 = $0.00000001818/token = $0.0182/MTok
Cursor: if $200 buys $600 payg-equivalent usage: treat as 3× subsidy until cap behavior changes.
But you correctly noted “dynamic usage / across models / unclear stabilization”. So do not hardcode those numbers as truth. Use them as priors.
C) Fixed-fee with prompt caps (Minimax: 300 prompts / 5 hours)
This is not token-based; convert prompts→tokens via observed averages:
Let:

P = 300 prompts per 5 hours
avgTok = E[tokens_total per prompt] from your logs
prompts per month:
5 hours window ⇒ 24/5 = 4.8 windows/day
prompts/day = 300 _ 4.8 = 1440
prompts/month ≈ 43,200 (30d)
So:
expected_tokens_month = prompts_month _ avgTok
EUC = monthly_fee / expected_tokens_month
This converges quickly once you have 1–2 days of real usage.
D) “Unlimited” (Copilot Student Pro: GPT-4.1, GPT-5 mini 0× usage)
You can’t price “unlimited” as $0 because it will dominate every decision and nuke quality.
Treat it as:

Hard preference for low cost
but with non-cost constraints:
rate/throughput limits
risk (availability policy changes)
output caps / tool limitations / context caps
quality thresholds per role
For cost index, set:
EUC = very_small_floor (e.g., $0.001/MTok)
but add Scarcity Shadow (below) to prevent degenerate always-pick behavior.
This keeps it “basically free” without breaking routing.

E) Promo / rotating free preview models
Same as unlimited, but with:
high volatility penalty (they disappear)
low trust until telemetry accumulates
2.2 Shadow pricing (budget control + fairness across plans)
Your router needs costs that reflect scarcity. Use two layers:
(1) Monthly budget shadow
Budget remaining:
budget*remaining = 600 - spend_to_date
expected_remaining = 600 * (days*remaining / days_in_month)
ratio = budget_remaining / expected_remaining
budget_shadow = 1 / max(ratio, ε)
If you overspend early, budget_shadow rises and makes everything “more expensive”.
(2) Plan quota shadow (prevents draining one plan instantly)
For plans that have effective quotas (Claude Max, Codex, Minimax, Cursor):
plan_ratio = remaining_tokens_est / expected_remaining_tokens_est
plan_shadow = 1 / max(plan_ratio, ε)
Then:
effective_cost = base_cost * budget*shadow * plan*shadow
For “unlimited” plans (Copilot), you can set plan_shadow based on:
observed throttling
or a constant mild penalty (so it’s preferred but not always)
2.3 Cursor / Claude Max / Codex sub: how to estimate “tokens covered” robustly
You said usage is dynamic and includes caching. So for each plan maintain:
monthly_fee
observed_spend_equivalent (if provider gives $ estimate)
observed_tokens_total (from your harness logs; includes cache hits)
effective_tokens_covered (latent variable)
Update daily with an EWMA:
tokens_covered_est[today] =
0.8 * tokens*covered_est[yesterday] +
0.2 * observed*tokens_total_today * scale_factor
Where scale_factor handles “cached tokens included”:
If cached tokens count as “free”, your “covered tokens” is larger than raw tokens.
If cached tokens still count to quota, your “covered tokens” is raw tokens.
You can infer this by watching whether heavy-cache days reduce future allowance. If unclear, default conservative.
Bottom line: your EUC becomes self-correcting using logs. 3) Speed Index: latency + conciseness + turns
You said conciseness matters. Do it explicitly.
For each offer & role maintain predictors:

p95_latency_ms
tokens_per_second
E[output_tokens | role, offer]
E[turns | role, offer] (optional, but useful)
Then:
gen_time = E_out_tokens / tokens_per_second
session_time = p95_latency_ms + gen_time + gamma \* E_turns
speed_score = session_time / median_session_time(role)
This will naturally penalize verbose models even if they’re low-latency. 4) Quality Index with spotty benchmarks (this is the real one)
You’re right: you’ll have missing benchmark values and inconsistent sets. If you naively average, rankings will be garbage.
Use a two-part quality system:

4.1 Offline Quality (from benchmark table you provide)
Represent benchmarks as a sparse matrix: score[offer, benchmark] with many missing.
Step A — Normalize per benchmark
For each benchmark b:
compute mean/STD across offers that have it
z-score:
z = (score - mean_b) / std_b
Step B — Impute missing values (simple but stable)
You don’t need fancy ML. Use shrinkage to family mean:
Let family = claude, gemini, gpt, glm, minimax, kimi, deepseek, qwen, etc.

For missing benchmark b:

imputed*z(offer,b) =
λ * mean*z(family,b) + (1-λ) * mean*z_global(b)
Where λ depends on how much family data exists:
if family has many points for b, λ→0.8
if not, λ→0.2
This keeps the index stable without pretending you know too much.
Step C — Role weights + missingness penalty
Compute role score:
offline_quality = Σ w_b(role) * z*or_imputed_z(offer,b)
Then apply a missingness confidence factor:
coverage = (# real benchmarks present for offer in role-set) / (total benchmarks in role-set)
offline_quality_adj = offline_quality * (0.6 + 0.4 * coverage)
So if a model is missing half the benchmarks, it can’t magically top-rank.
4.2 Online Quality (from your reality)
For coding roles, track:
test pass rate
lint/build success
“needed escalation” rate (how often user reruns on stronger model)
tool/schema adherence
Convert to 0–1, then:
online_quality = a*pass*rate + b*(1-escalation_rate) + c*adherence
4.3 Final Quality Index
Blend offline + online, with online taking over as data accumulates:
q = sigmoid( offline_quality_adj ) * (1 - ρ(n)) + online*quality * ρ(n)

ρ(n) = n / (n + k) (n = number of eval’d tasks for that offer+role)
So early on, benchmarks guide. Later, your data wins. 5) Routing: selecting Offer (not model) + fallback
You route to offerId directly.
Pipeline per request:

Determine role + hard constraints
Filter offers by capability + context + compliance
For each offer compute:
cost_score
speed_score
quality_score
Pareto prune
Lexicographic pick (you said baseline hard constraints then optimize order)
Generate fallback chain conditioned on failure types:
429/quota → different plan/provider
timeout → fastest next
schema fail → best adherence
quality fail (tests) → escalate quality tier 6) How “model → provider” could work (and why I’d still do Offer-first)
Two-stage approach:
Stage 1: pick modelId based on quality
Stage 2: pick provider based on cost/availability
Problem: provider differences change feasibility (quota, throttles, cached tokens, region latency). You’d end up re-evaluating anyway.
So: Offer-first is correct.

If you still want the conceptual separation, do this:

pick ModelGroup first (a “virtual model” that’s a set of offers)
then pick offer within that group
…but the math should still be computed on offers. 7) Using your ground truths explicitly (how they map)
Plans you listed → how to encode
Claude Max $200 → plan:fixed_bucket with prior 3B tok/mo
Codex $200 → plan:fixed_bucket prior 11B tok/mo
Cursor $200 → plan:subsidized_payg (3× value prior) + learn from logs
Minimax $40 → plan:prompt_rate_limited → convert via observed avg tokens
Copilot student unlimited GPT-4.1 & GPT-5 mini → plan:unlimited with mild penalty + constraints
GLM Max $80 → likely fixed bucket or prompt-limited; learn EUC from logs
Gemini premium $20 (antigravity free) → treat as fixed bucket / unlimited depending on actual limits; learn from logs
Promo harnesses → plan:volatile_free with high volatility penalty and low initial trust 8) Example: a tiny catalog snippet in “Offer-first JSON”
{
"offers": [
{
"offerId": "copilot:student:gpt-5-mini",
"modelFamily": "gpt",
"cap": { "tools": true, "json": true, "maxContext": 128000 },
"planId": "copilot-student",
"pricing": { "type": "unlimited", "eucPerMTokUsd": 0.001 },
"risk": { "volatility": 0.3 },
"telemetry": { "p95ms": 900, "tps": 120, "err": 0.02 }
},
{
"offerId": "codex:sub:gpt-5.3-codex-medplus",
"modelFamily": "gpt",
"cap": { "tools": true, "json": true, "maxContext": 256000 },
"planId": "codex-sub",
"pricing": { "type": "fixed_bucket", "feeUsd": 200, "priorTokPerMonth": 11000000000 },
"telemetry": { "p95ms": 1400, "tps": 90, "err": 0.01 }
}
]
}
If you want the next deliverable
I can output:
Canonical schemas for Plan, Offer, TelemetrySnapshot, EconomicsSnapshot, QualitySnapshot
A worked example calculating effective cost for 3 offers under your plans (including Minimax prompt caps and Copilot unlimited)
The exact Pareto + lexicographic selection pseudocode and fallback chain rules
Pick one and I’ll drop it in.

You said:
Yes, note for glm and copilot GitHub Copilot Free

For developers looking to get started with Copilot.

Includes up to 2,000 inline suggestions in IDEs per month
Includes up to 50 premium requests per month
Designed to give you a limited taste of Copilot's capabilities
No subscription or payment required
Intended for personal use only, not for users managed by an organization or enterprise
Great for developers who want to explore Copilot's capabilities before upgrading to a paid plan
GitHub Copilot Pro

For developers who want more flexibility, including unlimited completions and access to additional models.

Includes unlimited completions in IDEs
Access to Copilot Chat and additional models
Includes up to 300 premium requests per month (additional at $0.04 USD each)
Free for verified students, teachers, and maintainers of popular open source projects
GitHub Copilot Pro+

For developers who need maximum flexibility, premium access to available models, and expanded request limits.

Everything in Copilot Pro, plus:

Full access to all available models in Copilot Chat
Up to 1,500 premium requests per month (additional at $0.04 USD each)
Priority access to advanced AI capabilities
Ideal for AI power users and developers who want cutting-edge tools

Glm plan is 3x usage compared to CC on paper.

ChatGPT said:
Got it. This changes two big things:
Copilot isn’t “unlimited tokens.” It’s “unlimited completions” + metered premium requests (300/mo for Pro; 1500/mo for Pro+; extra at $0.04/request).
GLM plan being “3× usage vs CC” means we model it as a fixed bucket with a prior capacity multiplier, then let logs converge.
Below is the concrete deliverable you asked for: canonical schemas + worked examples + routing pseudocode—with Copilot handled correctly.

1. Canonical Schemas (what you store)
   1.1 Plan schema
   A plan is how you turn subscriptions/prompt-caps into an Effective Unit Cost (EUC) and a shadow price.
   {
   "planId": "copilot-pro",
   "type": "premium_request_bucket",
   "monthlyFeeUsd": 0,
   "resetsAt": "2026-03-01T00:00:00Z",
   "entitlements": {
   "premiumRequestsIncluded": 300,
   "premiumRequestOverageUsd": 0.04,
   "unlimitedCompletions": true,
   "inlineSuggestionsIncluded": null
   },
   "observed": {
   "premiumRequestsUsed": 37,
   "avgTokensPerPremiumRequest": 18000,
   "avgOutTokensPerPremiumRequest": 2500,
   "avgInlineTokensPerCompletion": 80
   },
   "policy": {
   "shadowEpsilon": 0.12,
   "riskVolatility": 0.2
   }
   }
   Plan types you need
   payg_token (OpenRouter payg, direct APIs)
   fixed_bucket_tokens (Claude Max, Codex “~11B tokens”, GLM “3× usage”)
   premium_request_bucket (Copilot Pro/Pro+/Free premium request caps)
   prompt_rate_limited (Minimax “300 prompts / 5 hours”)
   volatile_free (promo/preview models)
   1.2 Offer schema (routable unit)
   Offer = provider+model+region+plan. This is what the router selects.
   {
   "offerId": "copilot:gpt-5-mini:chat",
   "modelId": "gpt-5-mini",
   "provider": "copilot",
   "endpoint": "openai_compat://copilot/chat/completions",
   "region": "us",
   "planId": "copilot-pro",
   "capabilities": {
   "tools": true,
   "json": true,
   "vision": false,
   "maxContextTokens": 128000,
   "maxOutputTokens": 8192
   },
   "limits": {
   "rpm": 60,
   "tpm": 200000,
   "concurrency": 4
   },
   "pricingHint": {
   "type": "derived_from_plan"
   }
   }
   1.3 Snapshot schemas (hot path reads only snapshots)
   Router reads immutable snapshots (fast + deterministic).
   EconomicsSnapshot

{
"asOf": "2026-02-18T07:00:00Z",
"global": { "budgetRemainingUsd": 412.30, "budgetShadow": 1.15 },
"plans": {
"copilot-pro": {
"shadow": 1.02,
"effectiveUnitCost": { "inPerMTokUsd": 0.09, "outPerMTokUsd": 0.09 },
"premiumRequestsRemaining": 263
},
"codex-sub": {
"shadow": 1.30,
"effectiveUnitCost": { "inPerMTokUsd": 0.02, "outPerMTokUsd": 0.02 }
}
},
"offers": {
"copilot:gpt-5-mini:chat": {
"effectiveUnitCost": { "inPerMTokUsd": 0.09, "outPerMTokUsd": 0.09 }
}
}
}
TelemetrySnapshot
{
"offers": {
"copilot:gpt-5-mini:chat": { "p95ms": 1100, "tps": 110, "errRate": 0.02, "jsonAdherence": 0.98 },
"codex:gpt-5.3-codex-medplus": { "p95ms": 1500, "tps": 90, "errRate": 0.01, "jsonAdherence": 0.995 }
}
}
QualitySnapshot
{
"offers": {
"copilot:gpt-5-mini:chat": { "code*complex": 0.78, "code_simple": 0.84 },
"codex:gpt-5.3-codex-medplus": { "code_complex": 0.88, "code_simple": 0.90 }
},
"confidence": {
"copilot:gpt-5-mini:chat": { "code_complex": 0.55 },
"codex:gpt-5.3-codex-medplus": { "code_complex": 0.82 }
}
} 2) How we compute Effective Unit Cost (EUC) per plan
2.1 Fixed bucket (Claude Max / Codex / GLM)
You gave priors:
Claude Max: $200 for ~3B tokens/mo
Codex: $200 for ~11B tokens/mo
GLM: “3× usage compared to CC on paper” → treat as bucket = 3 × Claude prior, unless you give better.
Baseline EUC
EUC = monthlyFee / expectedTokensCovered
Example:
Claude: 200 / 3e9 = $0.0667/MTok
Codex: 200 / 11e9 = $0.0182/MTok
GLM (3× Claude): 80 / (3 * 3e9 _ (80/200?)) ← careful:
You didn’t give GLM $→tokens prior directly.
“3× usage vs CC” likely means: for comparable spend, 3× capacity.
If Claude is $200, GLM is $80. Two possibilities:
GLM $80 gives 3× Claude Max usage (unlikely but possible)
GLM $80 gives 3× GLM base plan vs some other GLM plan
So: don’t guess. Use a prior multiplier, but let logs dominate quickly.
Correct approach for GLM: store priorTokensCovered as unknown and learn from observed usage:
start with: priorTokensCovered = 3e9 _ (80/200) \_ 3 = 3.6e9 (a placeholder prior)
then update with your telemetry (EWMA)
2.2 Copilot Pro/Pro+/Free (premium requests)
Copilot isn’t token metered. It’s request-metered (for chat / premium models).
You convert premium request budgets into token budgets using your own observed averages.

Let:

includedPremiumRequests = 300 (Pro) or 1500 (Pro+)
overage = $0.04/request
observed avg tokens per premium request:
avgInTok, avgOutTok (from your harness logs)
Effective cost per token for Copilot premium
If you’re within included requests:
marginal $ is “0” (since student plan covers it), but scarcity exists.
So model it as:
shadow cost derived from the replacement price (overage)
Compute implied $/token using overage:
implied*cost_per_request = 0.04
avg_total_tokens = avgInTok + avgOutTok
EUC_implied = 0.04 / avg_total_tokens
Example if avg_total_tokens = 20,000:
EUC = 0.04 / 20000 = $0.000002/token = $2/MTok
Then apply request scarcity shadow based on remaining premium requests:
plan_ratio = remaining_requests / expected_remaining_requests_today
shadow = 1 / max(plan_ratio, ε)
effective_cost = EUC_implied * shadow
This does two crucial things:
Copilot premium feels cheap when you have a lot left
It becomes expensive near the end of the month, preventing accidental depletion
Copilot “unlimited completions”
Treat completions separately as a different “offer type” with:
tiny cost
but limited to IDE inline completion use-case (short outputs only)
So you’ll have:
copilot:_:inline_completion offers (no premium request usage)
copilot:*:chat offers (consumes premium requests)
That separation stops you from using “completion-unlimited” as a loophole for heavy chat. 3) Speed index (with conciseness baked in)
Per offer and role:
p95_latency_ms
tokens_per_second
E_out_tokens(role, offer)
optional E_turns(role, offer)
gen_time = E_out_tokens / tps
session_time = p95_latency + gen_time + gamma*E_turns
speed_score = session_time / median_session_time(role)
You train E_out_tokens from logs, by role. 4) Quality index with missing benchmarks (stable even when spotty)
This is the approach that won’t break when you have sparse manual benchmark entries:
4.1 Normalize benchmark values per benchmark
Z-score per benchmark where present.
4.2 Impute missing using shrinkage (family mean → global mean)
z_hat = λ _ mean*z(family, b) + (1-λ) * mean*z(global, b)
4.3 Role-weighted sum + coverage penalty
offline_quality = Σ w_b(role) * z*or_z_hat
coverage = (# real benchmarks present) / (# benchmarks used by role)
offline_adj = offline_quality * (0.6 + 0.4*coverage)
4.4 Blend with online outcomes as they accumulate
quality = (1-ρ(n))*sigmoid(offline*adj) + ρ(n)\_online_quality
ρ(n)=n/(n+k) 5) Worked Example: Routing to an Offer (and thus provider)
Assume a code_complex request with:
inTok = 12,000
outTok = 2,500
Candidates:
codex-sub:gpt-5.3-codex-medplus (fixed bucket)
copilot:gpt-5-mini:chat (premium request bucket)
openrouter:deepseek-v3.2 (payg)
(plus others)
5.1 Compute cost per offer
A) Codex sub (fixed bucket EUC)
EUC ~ $0.0182/MTok (prior) × shadow (say 1.3)
Total tokens = 14,500
base = 14500 * (0.0182 / 1,000,000) = $0.000264
effective = base _ 1.3 = $0.000343
Basically free (because your assumed token bucket is huge). If that’s wrong, logs will correct EUC upward.
B) Copilot chat (premium requests)
Suppose avg total tokens per premium request = 20,000
Implied EUC = 0.04/20000 = $2/MTok
If shadow=1.1:
base = 14500 _ (2 / 1,000,000) = $0.029
effective = 0.029 _ 1.1 = $0.032
C) OpenRouter payg
Use token prices directly; maybe it’s $0.5/MTok in, $1/MTok out (example). Then:
base = 12000_(0.5/1e6) + 2500*(1/1e6) = 0.006 + 0.0025 = $0.0085
effective = base * budget_shadow(1.15) \* plan_shadow(1.0) = $0.0098
Now you see why offer-first matters: Copilot chat may not be cheapest despite “free student”, because its premium requests are scarce and have an implicit replacement cost.
5.2 Speed + Quality
You compute speed_score and quality_score similarly per offer.
5.3 Pareto + lexicographic
If your order is:
quality
cost
speed
You’ll likely choose:
Codex sub for intense coding (if quality high and cost near-zero)
Copilot chat only when you’re not burning premium requests too quickly
OpenRouter as flexible mid-cost fallback
And then execution is trivial: the offer contains provider endpoint and auth mapping. 6) Routing pseudocode (Offer-first)
route(request):
role = request.role
tokIn, tokOut = estimate_tokens(request)

offers = load(OfferSnapshot)
econ = load(EconomicsSnapshot)
tel = load(TelemetrySnapshot)
qual = load(QualitySnapshot)

candidates = []
for offer in offers:
if !capability_ok(offer, request.hard): continue
if offer.cap.maxContext < request.hard.minContextTokens: continue

    q = qual.score(offer, role) * qual.confidence(offer, role)
    if q < request.hard.minQuality: continue

    cost = effective_cost_usd(offer, tokIn, tokOut, econ)
    if cost > request.hard.maxCostUsd: continue

    speed = speed_score(offer, role, tel, tokOut)
    candidates.append({offer, q, cost, speed})

pareto = pareto_frontier(candidates)

chosen = lexicographic(pareto, order=["q_desc", "cost_asc", "speed_asc"])

chain = build_fallback_chain(pareto, chosen, request.hard)

return execute_with_fallback(chain) 7) How provider/model additions work (mechanically)
Add new provider:
Adapter implements:
list models/offers
pricing (or “unknown”)
usage/quota endpoints (or “unknown”)
execute
System creates offers in inactive or canary
Telemetry learns speed/error immediately
Cost:
if payg → immediate
if sub/promo → start with priors, learn EUC from usage
Quality:
start with imputed offline from family/global
improves as online outcomes collected
Then it participates in Pareto.
Add new model under existing provider:
just new offers; same machinery. 8) Budget moving around (how it reallocates)
You have:
global monthly budget $600
plus plans with fixed fees
You track variable spend separately from fixed subscription spend.
Each night:

compute burn vs expected
adjust budget_shadow
optionally adjust role caps (code_complex gets protected vs fast_chat)
Also per plan:
compute plan shadow from remaining quota/premium requests
this “moves budget around” automatically by changing effective costs.
If Copilot premium requests are low, it becomes “expensive” and router moves traffic to Codex/Claude/GLM/OpenRouter offers.
If you want me to lock this into a final spec
Answer one thing: Are you on Copilot Pro (student) or Pro+ (student)?
You mentioned “student pro for free” earlier, but you just pasted Free/Pro/Pro+ tiers.
If you don’t answer, I’ll assume Copilot Pro (300 premium req/mo, unlimited completions) and proceed.

You said:
Copilot isn’t “unlimited tokens.” It’s “unlimited completions” + metered premium requests (300/mo for Pro; 1500/mo for Pro+; extra at $0.04/request).

Premium requests are billed to models at a multiple, e.g sonnet is 1x, opus 2x, gemini 0.1x, haiku 0.33x, gpt 4.1, gpt 5 mini pseicifcally are marked as "0x" hence they dont count against usage

ChatGPT said:
Perfect — that “multiplier” + “0x” detail is exactly how to model Copilot correctly.
Core change:
Copilot premium usage isn’t “requests/month”. It’s premium units/month where each model consumes multiplier units, and some models are 0x (free in units).
So the plan becomes a weighted unit bucket, not a request bucket.

1. Update the Plan Model for Copilot
   Copilot Plan = “Premium Unit Bucket”
   unitsIncluded = 300 (Pro) or 1500 (Pro+)
   unitOverageUsd = 0.04 per unit (or per request unit; treat as per unit)
   Each model has unitMultiplier:
   Sonnet = 1.0x
   Opus = 2.0x
   Gemini = 0.1x
   Haiku = 0.33x
   GPT-4.1 = 0x
   GPT-5 mini = 0x
   Plan schema (updated)
   {
   "planId": "copilot-pro-student",
   "type": "weighted_unit_bucket",
   "monthlyFeeUsd": 0,
   "resetsAt": "2026-03-01T00:00:00Z",
   "entitlements": {
   "premiumUnitsIncluded": 300,
   "premiumUnitOverageUsd": 0.04,
   "unlimitedCompletions": true
   },
   "unitMultipliers": {
   "claude-sonnet-4.6": 1.0,
   "claude-opus-4.6": 2.0,
   "claude-haiku-4.5": 0.33,
   "gemini-3-pro": 0.1,
   "gemini-3-flash": 0.1,
   "gpt-4.1": 0.0,
   "gpt-5-mini": 0.0
   },
   "observed": {
   "premiumUnitsUsed": 37.2,
   "avgTokensInByModel": { "claude-sonnet-4.6": 12000, "gemini-3-pro": 9000 },
   "avgTokensOutByModel": { "claude-sonnet-4.6": 2400, "gemini-3-pro": 1800 }
   }
   }
2. Offer Catalog Must Encode Copilot “Unit Multiplier”
   Each Copilot offer carries unitMultiplier (or references via plan map).
   {
   "offerId": "copilot:claude-opus-4.6:chat",
   "provider": "copilot",
   "modelId": "claude-opus-4.6",
   "planId": "copilot-pro-student",
   "pricingHint": { "type": "copilot_units", "unitMultiplier": 2.0 },
   "capabilities": { "tools": true, "json": true, "maxContextTokens": 200000 }
   }
   And for 0x models:
   {
   "offerId": "copilot:gpt-5-mini:chat",
   "provider": "copilot",
   "modelId": "gpt-5-mini",
   "planId": "copilot-pro-student",
   "pricingHint": { "type": "copilot_units", "unitMultiplier": 0.0 }
   }
3. Copilot Effective Cost Function (the exact math)
   3.1 Convert “unit overage” to $/token (implied EUC)
   Since you don’t know token pricing from Copilot, you treat the replacement cost as the overage per unit.
   For a request with predicted tokens:

Tin, Tout
total tokens T = Tin + Tout
If model multiplier = m:
units consumed = m
Implied $/token (if you were in overage world):
implied*EUC_per_token = (unitOverageUsd * m) / T
But within included units, marginal cost is “0” — so you apply shadow pricing to reflect scarcity.
3.2 Shadow price for unit scarcity
Let:
included units = U*total
units used so far = U_used
remaining units = U_rem = U_total - U_used
expected remaining at this point in month = U_exp (based on day-of-month pacing)
ratio = U_rem / max(U_exp, ε)
shadow = 1 / max(ratio, ε)
So as you fall behind pace (using too many units early), shadow rises.
3.3 Final effective cost for Copilot premium offers
effective_cost = implied_cost * shadow _ budget_shadow
Where:
implied_cost = unitOverageUsd _ m
Important: this cost is per request, not per token, because Copilot charges “units”, not tokens.
So do:

effective*cost_usd = (0.04 * m) \_ shadow \* budget_shadow
This is clean, stable, and matches how the product is actually metered.
3.4 Special case: m = 0x (GPT-4.1, GPT-5 mini)
If m = 0, then implied cost is $0.00.
But you still cannot let it dominate everything, so you add a non-monetary scarcity / risk term:

Use:

“free model penalty” = small constant + volatility
plus quality constraints
So:
effective_cost_usd = 0
effective_cost_score = floor_cost + volatility_penalty + opportunity_penalty
Where floor_cost is tiny (like $0.002 equivalent) just to prevent degenerate “always pick free” behavior during tie-breaks.
If you prefer purity: keep cost = 0 and rely entirely on quality thresholds + Pareto. But in practice, you’ll want a floor.

4. How this impacts routing behavior (exactly what you want)
   When you have lots of Copilot units left:
   Sonnet (1x) looks cheap
   Gemini (0.1x) looks extremely cheap
   Haiku (0.33x) cheap
   Opus (2x) expensive-ish
   When you’re running low:
   shadow spikes
   Copilot premium offers become “expensive”
   router shifts to:
   Claude Max / Codex sub buckets
   GLM Max
   OpenRouter payg
   self-host
   0x models:
   always available as last-resort cheap fallback
   but still won’t replace premium models for hard tasks if quality thresholds demand higher
5. Updated “Cost Index” summary (all plans unify)
   For any offer, effective_cost_usd(request) comes from one of:
   Token-based (payg):
   cost = Tin*p_in + Tout*p_out then × shadows
   Fixed bucket tokens (Claude/Codex/GLM):
   EUC = monthly_fee / tokens_covered_est
   cost = EUC*(Tin+Tout) then × shadows
   Rate-limited prompts (Minimax):
   same as bucket but tokens_covered derived from prompt capacity × avg tokens
   Copilot weighted units:
   cost = 0.04 * multiplier then × shadows
   if multiplier = 0 → cost floor only
   That’s it. One router, multiple economics.
6. Practical catalog example (Copilot + your other plans)
   Copilot Pro Student: 300 units/mo
   Offers:
   copilot:gpt-5-mini:chat multiplier 0x
   copilot:gpt-4.1:chat multiplier 0x
   copilot:claude-sonnet-4.6:chat multiplier 1x
   copilot:claude-opus-4.6:chat multiplier 2x
   copilot:gemini-3-pro:chat multiplier 0.1x
   copilot:haiku-4.5:chat multiplier 0.33x
   Now your router can numerically see:
   Gemini via Copilot is basically “3,000 requests worth” (300 / 0.1) before overage, if they allow it.
   Opus burns your units 2× as fast.
   Exactly what you want.
7. One more thing you should do (or this will still misroute)
   Copilot “premium units” are not equivalent across models in quality, so add a unit-efficiency feature:
   For each offer:

quality_per_unit = quality_score / unitMultiplier
This is not the main objective, but it’s a great tie-breaker when cost is dominated by Copilot scarcity.
For 0x models, define unitMultiplier=ε for computation (or skip).

8. What I need from you (only if you want precision, not required)
   Are you on Pro (300 units) or Pro+ (1500 units)?
   Confirm overage is $0.04 per unit (not per request regardless of units)
   If you don’t answer, I’ll assume Pro student (300 units) and $0.04 per unit.
   If you want next, I’ll produce:
   the exact EconomicsSnapshot builder logic for Copilot units + fixed token buckets
   plus a worked routing example where Copilot units are low mid-month and the router shifts load to Codex/Claude Max automatically.

You said:
Compile to unified PRD + Phased WBS\DAG and Technical ALD\ADR docket

ChatGPT said:
Good. Now we formalize this properly.
What follows is a unified PRD + phased WBS/DAG + Technical ALD + ADR docket for your LLM routing control plane.

This is written like something you could drop into a serious internal design doc.

HELIOS ROUTER
Unified PRD + WBS/DAG + ALD + ADR Docket

1. PRODUCT REQUIREMENTS DOCUMENT (PRD)
   1.1 Product Name
   Helios Router — Cost-Aware Multi-Provider LLM Control Plane
   1.2 Problem Statement
   We operate across:
   Claude Max ($200)
   Codex Sub ($200)
   Cursor ($200)
   Copilot Pro Student (300 weighted units/mo)
   GLM Max ($80, ~3× usage prior)
   Minimax ($40, rate-limited prompts)
   Gemini Premium ($20)
   OpenRouter PAYG
   Promo/preview models
   Self-host (GPU rentals)
   Models change rapidly. Pricing structures differ:
   token-based
   fixed bucket
   weighted premium units
   prompt rate-limited
   unlimited completions (Copilot inline)
   volatile preview
   We need:
   A model-agnostic routing system that computes Speed, Cost, and Quality indices dynamically and routes at the offer (model+provider+plan) level under budget constraints.
   1.3 Objectives
   Functional
   Canonical offer catalog (provider+model+plan).
   Unified cost model (token, bucket, unit, rate-limited).
   Weighted premium unit modeling (Copilot).
   Stable quality index with sparse benchmarks.
   Telemetry-driven speed & verbosity model.
   Pareto-based routing with lexicographic selection.
   Budget pacing + shadow pricing.
   Fallback chain logic.
   Canary onboarding for new providers.
   Snapshot-driven deterministic hot path.
   Non-Functional
   Area Requirement
   Hot Path Latency < 5ms p95 routing decision
   Determinism Snapshot-based routing
   Extensibility New provider integration < 1 day
   Budget Safety Cannot exceed $600 monthly
   Observability Full route trace + economics
   Stability Sparse benchmark handling
   1.4 Optimization Axes
1. Speed Index
   Accounts for:
   p95 latency
   generation time (tokens/sec)
   verbosity (expected output tokens)
   expected turns
1. Cost Index
   Accounts for:
   token cost OR
   fixed bucket EUC OR
   Copilot weighted unit multiplier OR
   rate-limited prompt bucket
   shadow pricing (quota + budget pacing)
1. Quality Index
   Accounts for:
   normalized external benchmarks
   shrinkage-based imputation
   online task success
   role-specific weighting
   coverage penalty
   confidence weighting
   1.5 Routing Strategy
   Hard constraint filtering
   Compute objective vectors:
   minimize cost
   minimize speed
   maximize quality
   Pareto frontier
   Lexicographic final selection
   Fallback chain generation
   1.6 Budget Strategy
   Monthly variable budget: $600
   Split conceptually:

Fixed subscription fees tracked separately
Variable spend pool tracked daily
Budget pacing shadow:
budget_shadow = 1 / max(remaining / expected_remaining, ε)
Degraded mode triggered at:
85% monthly burn
or quota exhaustion 2. PHASED WBS + DAG
Phase 0 — Foundations
WBS
Canonical Schema Design
Offer Registry
Plan Types Modeling
Snapshot System
DAG
Schema → Offer Registry → Snapshot Engine
Schema → Plan Modeling → Economics Engine
Phase 1 — Economics Engine
Deliverables
Fixed bucket EUC model
Copilot weighted unit model
Rate-limited prompt model
Shadow pricing engine
Budget pacing engine
DAG
Plan Schema
↓
EUC Calculators
↓
Shadow Pricing
↓
Economics Snapshot
Phase 2 — Telemetry + Speed Modeling
Deliverables
Per-offer telemetry ingestion
p50/p95 latency windows
tokens/sec estimation
verbosity predictor
session_time estimator
DAG
Execution Logs → Telemetry Aggregator → Speed Model → Snapshot
Phase 3 — Quality Engine
Deliverables
Sparse benchmark matrix
Z-score normalization
Family shrinkage imputation
Coverage penalty
Online performance blending
Confidence weighting
DAG
Benchmarks → Normalizer → Imputer → Role Weighting
Execution Results → Online Metrics → Blend
Phase 4 — Router Core
Deliverables
Hard constraint engine
Pareto frontier
Lexicographic selector
Fallback chain generator
Route trace
DAG
Snapshots → Filter → Score → Pareto → Select → Execute
Phase 5 — Provider Onboarding System
Deliverables
Adapter interface
Canary mode
Telemetry confidence gating
Auto-activation
Phase 6 — Budget Governance
Deliverables
Role-level budgets
Rebalancing job
Degraded mode logic
Alerting 3. TECHNICAL ALD (Architecture)
3.1 System Topology
┌─────────────────────────┐
│ Client / CLI │
└─────────────┬───────────┘
│
▼
┌─────────────────────┐
│ Router API │
└─────────────┬───────┘
│
┌───────────────┼───────────────┐
▼ ▼ ▼
Hard Filter Scoring Engine Fallback Engine
│
▼
Provider Adapter
│
▼
Execution + Logs
3.2 Control Plane
Offer Registry
Plan Engine
Shadow Pricing Engine
Budget Engine
Telemetry Aggregator
Quality Engine
Snapshot Builder
Snapshots are immutable and hot-loaded into Router.
3.3 Economics Engine (Copilot Example)
units_remaining = total_units - used_units
ratio = units_remaining / expected_remaining_units
shadow = 1 / max(ratio, ε)

effective*cost = 0.04 * multiplier \_ shadow \* budget_shadow
For 0x models:
effective_cost = floor_cost + volatility_penalty
3.4 Quality Engine (Sparse Safe)
z = (score - mean_b) / std_b

if missing:
z*hat = λ * mean*family + (1-λ) * mean_global

offline = Σ w*b * z*hat
coverage = present_benchmarks / total_benchmarks
offline_adj = offline * (0.6 + 0.4\*coverage)

quality = (1-ρ)*sigmoid(offline_adj) + ρ*online_score
3.5 Routing Algorithm (Final)
for offer in offers:
if !hard_constraints: continue

    cost = effective_cost(offer)
    if cost > maxCost: continue

    speed = speed_score(offer)
    quality = quality_score(offer)

collect candidates

pareto = non_dominated(candidates)

selected = lexicographic(pareto, order=[quality, cost, speed])

execute_with_fallback(selected) 4. ADR DOCKET
ADR-001: Offer-First Routing
Decision: Route to offer (model+provider+plan) instead of model.
Rationale: Economics and limits differ per provider.
Status: Accepted.
ADR-002: Pareto before Scalar Weighting
Decision: Use Pareto frontier before lexicographic selection.
Rationale: Avoid premature weighting bias.
Status: Accepted.
ADR-003: Copilot Weighted Unit Modeling
Decision: Treat Copilot as weighted unit bucket, not token meter.
Rationale: Align with actual billing semantics.
Status: Accepted.
ADR-004: Shadow Pricing
Decision: Apply pacing-based shadow multipliers.
Rationale: Prevent early quota exhaustion.
Status: Accepted.
ADR-005: Sparse Benchmark Imputation via Shrinkage
Decision: Family-weighted imputation for missing benchmarks.
Rationale: Stability under incomplete release data.
Status: Accepted.
ADR-006: Snapshot-Based Hot Path
Decision: Router reads immutable snapshots only.
Rationale: Determinism + performance.
Status: Accepted.
ADR-007: 0x Model Handling
Decision: Assign floor cost + volatility penalty.
Rationale: Prevent degenerate always-free selection.
Status: Accepted. 5. Final Architecture Summary
This system:
Treats models as commodities
Treats plans as economic engines
Treats providers as execution backends
Treats routing as constrained multi-objective optimization
Treats Copilot correctly as weighted premium units
Survives rotating promo models
Keeps spend under $600
Scales with new providers
If you want next, I can:
Convert this into a database schema + migrations
Or produce a Go / TS service layout
Or produce a 30-day simulated spend evolution under real workloads
Or produce a risk analysis (failure modes + mitigation)

You said:
cerebras offers very fast models, NVIDIA NIM offers step 3.5 fast and also good, Morph and some competitors offer niche small task (e.g. file edit\write) models at 3000+ tok\s research how they can fit in

ChatGPT said:
Here’s how Cerebras, NVIDIA NIM (Nemotron/LLM acceleration), and high-throughput specialist models like the 3 000 + tokens/sec offerings can fit into your Helios Router system—structured so you can place them into your catalog, indices, and routing pipelines with minimal guesswork.

1. Who They Are & What They Offer (as of early 2026)
   🧠 Cerebras (Wafer-Scale Engines & High-Throughput LLMs)
   Cerebras hardware (Wafer Scale Engine) is designed for very high throughput inference, significantly exceeding GPU offerings for certain models. Its systems have been shown to outperform GPU inference by large factors and support models at thousands of tokens per second.
   OpenAI released GPT-5.3-Codex-Spark optimized for Cerebras chips, aimed at code editing and interactive coding workflows with throughput exceeding 1 000 tokens/sec under optimal conditions.
   Independent benchmarks (on Cerebras inference platforms) list models like GPT-OSS-120B pushing ~3 000 tokens/s and smaller models like llama3.1-8B at ~2 200 tokens/s on these systems.
   Where this fits in your router:
   Cerebras-backed offers are excellent candidates for high-throughput, fast interactive tasks (fast editing, code walk-through, search/assist) where latency and throughput outweigh marginal quality differences.
   🚀 NVIDIA NIM Microservices (Nemotron & LLM Acceleration)
   NIM microservices are prebuilt, optimized containers that accelerate inference on NVIDIA GPUs (RTX AI PCs, cloud GPUs), often improving throughput dramatically over stock model performance.
   They include optimized LLM deployments (e.g., Llama 3.1 8B, 70B) as well as other AI components. In the context of your system, NIM variants can provide fast inference and pipeline acceleration especially when paired with TensorRT-LLM optimizations.
   Where this fits:
   NIM inference is a great option for self-hosted or hybrid offers—particularly where you’ll run mid-tier models locally for lower cost and high throughput. Their speed gains directly translate into better Speed Index scores.
   🧩 Niche Small-Task Models (e.g., Morph, terEffic FPGA)
   Academic and industrial research like TerEffic shows how specialized accelerators (like FPGAs with ternary quantization) can push tens of thousands of tokens/sec for small models. These aren’t mainstream yet commercially, but they illustrate a trend: specialized hardware can do extreme throughput for narrow tasks.
   Independent content on 3 000 tokens/sec LLM inference confirms that architectures optimized for throughput (including FPGA or custom ASIC) are real and achievable.
   Where this fits:
   These models/hardware are ideal for specialist “micro-offers” in your catalog—fast but capability-limited. They shine in tasks like:
   code snippet editing
   diff application
   small file transformation
   regex rewrite
   prompt filtering/triage
2. How to Include Them in the Helios Catalog
   You want your catalog to represent practical routable offers. For these high-throughput systems, we extend the existing offer schema like this:
   Example Unified Catalog Entries
   🧱 Cerebras High-Throughput Offer
   {
   "offerId": "cerebras:codex-spark:fast",
   "provider": "cerebras",
   "modelId": "gpt-5.3-codex-spark",
   "endpoint": "https://api.cerebras.ai/v1/inference/codex-spark",
   "capabilities": {
   "tools": true,
   "jsonMode": true,
   "vision": false,
   "maxContextTokens": 200000,
   "specializedThroughput": true
   },
   "pricing": {
   "inputPerMTokUsd": 5.0,
   "outputPerMTokUsd": 25.0
   },
   "limits": {
   "throughputTokensPerSec": 1200
   }
   }
   Throughput hints (e.g., throughputTokensPerSec) feed directly into the Speed Index model, giving Cerebras offers a strong bias for throughput-heavy use cases.
   Tuning the cost coefficients for throughput (see next section) ensures consistent ranking in the Pareto decision.
   🤖 NVIDIA NIM Optimized Offer
   {
   "offerId": "nvidia:nim:llama3.1-8B",
   "provider": "nvidia",
   "modelId": "llama3.1-8b",
   "endpoint": "https://api.nvidia.ai/nim/llama3.1-8b",
   "capabilities": {
   "tools": true,
   "jsonMode": false,
   "maxContextTokens": 8192
   },
   "pricing": {
   "inputPerMTokUsd": 1.20,
   "outputPerMTokUsd": 3.50
   },
   "limits": {
   "throughputTokensPerSec": 5200
   }
   }
   The throughputTokensPerSec → used to compute a throughput boost factor in your speed predictor.
   NIM microservices can be self-hosted or via a cloud provider API, integrated through your OpenAI-compatible gateway.
   ⚡ High-Speed Specialist Micro-Model (Morph-style)
   {
   "offerId": "morph:small-edit:fast-tx",
   "provider": "morph",
   "modelId": "morph-small-edit-3000",
   "endpoint": "https://api.morph.ai/v1/llm/fast-small-edit",
   "capabilities": {
   "tools": false,
   "jsonMode": false,
   "maxContextTokens": 4096,
   "specializedTask": "snippet_edit"
   },
   "pricing": {
   "inputPerMTokUsd": 0.25,
   "outputPerMTokUsd": 0.80
   },
   "limits": {
   "throughputTokensPerSec": 3000
   }
   }
   Micro-models like these should be included as specialist offers: cheap, high throughput, but capability limited (e.g., poor tool support, narrow context).
   They help reduce overall cost on “small jobs” by quickly handling simple edits or transformations.
3. How They Fit into Your Scoring System
   🧠 Speed Index Enhancement
   Add a throughput factor:
   session_time = p95_latency + (expected_output_tokens / tokens_per_second)

- gamma \* expected_turns
  and let tokens_per_second be sourced from offer metadata (throughputTokensPerSec).
  High throughput → smaller session_time → better rank.
  Large throughput models like Cerebras and NIM→optimized variants will score very well for “turns with many tokens”, e.g., code expansion, file rewrite tasks.

💰 Cost Index Calibration
You should compute effective cost with a throughput multiplier:
cost_per_effective_unit = unit_cost / throughput_factor
Where:
throughput_factor = tokens_per_second / median_tokens_per_second
This reflects “you get more for your spend if the model is faster”.
Important: tie this into the shadow pricing logic so that throughput advantage doesn’t completely override quality when quality is critical.

📊 Quality Index Considerations
Even if throughput is very high, a specialist model’s quality score must reflect its niche nature.
For example:

Morph-style micro edit model: excellent for snippet edits → high quality for specific role (edit/snippet) but poor on “complex reasoning”.
NIM-accelerated Llama variants: balanced quality/throughput, good for bulk but perhaps lower on deep reasoning tasks than flagship models.
Assign role-specific benchmark weights accordingly. 4) How to Dynamically Incorporate These in Pareto Routing
Your existing router algorithm integrates these models naturally:
Hard Filter
For tasks requiring tools or multi-file reasoning, micro-models get filtered out.
Indices
Speed: computed using throughput tokens/sec
Cost: effective cost with shadow multipliers
Quality: role-adjusted
Pareto Frontier
Throughput-high, cheap offers will dominate for “high-volume, low-complexity” roles
Quality-high, slower models will still dominate for “complex reasoning / agentic tasks”
Lexicographic Tie-Break
Example: first requirement = quality
But for roles like “file rewrite” or “snippet edit”, your router can reorder to prefer speed before quality. 5) Provider/Hardware Metadata Fields You Should Add
To support this seamlessly in your catalog and scoring:
offer {
throughputTokensPerSec: number,
throughputCategory: "ultra_fast" | "fast" | "normal",
latencyProfile: { p50: ms, p95: ms },
qualityBuckets: { edit: score, code: score, reasoning: score }
}
This gives your indices the raw numbers they need for accurate routing. 6) When to Use Each
Use Case Best Fit
High-speed code editing Cerebras Codex-Spark
Mass code rewrites / build chat NIM accelerated mid-tier models
Small snippet transforms Morph / specialist micro-models
Deep reasoning or multi-file code Claude / GPT5.3 / Codex flagship
Large context parsing Larger models on slower hardware 7) Integration Strategy (Practical)
Catalog ingestion
Add Cerebras/NIM/Morph offers with throughput metadata
Benchmarks
Manually assign initial quality scores per role
Use your online telemetry to improve over time
Cost modeling
For cloud providers, pay-per-token as usual
For self-hosted NIM variants, derive cost from compute hours
For Cerebras, use “tokens/sec \* price/sec” if offered by vendor
Routing experiments
Tag roles that benefit from throughput capture
Gradually tune balancing coefficients between quality/cost/speed
Summary
Cerebras = high throughput, great for interactive editing tasks.
NVIDIA NIM microservices = accelerated inference for local/cloud LLMs, strong throughput gains.
Micro specialist models (Morph) complement your offerings via niche tasks where speed > general quality. (industry trend, inferred)
All of these can be folded into your LLM Routing system as specialized offers with appropriate throughput and role-specific quality metadata so the optimizer can place them correctly.
If you want, I can also give you concrete cost modeling guidelines for self-hosted NIM/Cerebras (e.g., tokens/sec → effective $/MTok) so you can simulate Helios Router spend precisely with these new options.

You said:
Do proper research plz

ChatGPT said:

Thought for 17m 31s

Answer now
You’re right to call that out. “Fast” in LLM-land is overloaded, and if you don’t model it correctly you’ll route to the wrong thing (or blow quotas).
Below is actual, sourced research on Cerebras, NVIDIA NIM / build.nvidia.com + Step 3.5 Flash, and Morph + competitors (Relace), and then exactly how they fit into your offer-first router (catalog + indices + pipelines + role design).

1. Reality check: “tokens/sec” is not one metric
   Vendors and communities mix at least four different things:
   TTFT (time to first token)
   ITL (inter-token latency)
   Output tokens/sec (streaming speed after first token)
   Aggregate throughput under concurrency (tokens/sec across many requests)
   NVIDIA’s own benchmarking primer explicitly calls out TTFT, end-to-end latency, ITL, tokens/sec, requests/sec as separate metrics, and emphasizes that input/output length distributions matter for prefill vs generation.
   Router implication: don’t store one “toks_per_sec”. Store a profile:

ttft_p50/p95
itl_p50/p95
tps_stream_p50/p95 (per request stream)
tps_agg_at_concurrency (system throughput) 2) Cerebras: what they actually offer, with numbers you can ingest
2.1 Cerebras Inference (pay-per-token) is real and cheap for some models
Cerebras’ docs for Llama 3.1 8B list:
~2200 tokens/sec
$0.10 / 1M tokens input
$0.10 / 1M tokens output
free tier and developer tier rate-limit info.
Their press release (Aug 27, 2024) claims:
1,800 tok/s for Llama 3.1 8B and 450 tok/s for 70B
pay-as-you-go pricing starting at $0.10/M (8B) and $0.60/M (70B)
and cites Artificial Analysis verification of speeds and “quality evaluation results in line with native 16-bit precision”.
2.2 Cerebras “Code” subscriptions are daily-token-capped, not unlimited
Cerebras Code FAQ states:
Code is a subscription access to high-speed code generation LLMs (powered by Qwen3-Coder) and runs “at up to 2,000 tokens/sec”
Code Pro ($50/mo): 24M tokens/day, 1,000,000 TPM, 50 RPM
Code Max ($200/mo): 120M tokens/day, 1,500,000 TPM, 120 RPM
and it explains queue time / utilization variance and burst/RPS causing 429s.
Their pricing page also warns preview models can be discontinued at short notice (important for your “volatility” risk field).
2.3 Cerebras also runs very-high-throughput frontier-ish open models
Cerebras blog: OpenAI’s gpt-oss-120B “available on Cerebras Cloud” with:
3000 tokens/sec
$0.25/M input, $0.69/M output
128k context
MoE architecture details.
Router implication: Cerebras gives you:
Pay-per-token offers (clean economics)
Subscription daily-bucket offers (need pacing)
Speed that can dominate speed index for long outputs
Queue-time and burst limits you must model (or you’ll route into 429 storms) 3) NVIDIA NIM: what it is, what “fast” means here, and how Step 3.5 fits
3.1 NIM is primarily an optimized deployment layer (self-host/hybrid), not “one API”
NVIDIA NIM microservices are “prebuilt, optimized inference microservices” that expose standard APIs and can run on Kubernetes across NVIDIA GPU infra.
On the NIM microservices page they show a concrete example:

Llama 3.1 8B instruct on 1× H100 SXM with 200 concurrent requests
NIM ON: throughput 1201 tokens/s, ITL 32ms
NIM OFF: throughput 613 tokens/s, ITL 37ms
That throughput number is under concurrency; it’s a system throughput datapoint, not necessarily “one user sees 1201 tok/s”.
3.2 Step 3.5 Flash (StepFun) on NVIDIA build/NIM: fast-ish, but not 3000 tok/s
The NVIDIA model card for step-3.5-flash says:
MoE LLM by StepFun
196.81B total params, ~11B active per token
“real-time responsiveness with 100–300 tok/s throughput (peaking at 350 tok/s for coding tasks)”
So: yes, “fast” compared to many frontier reasoning models — but it’s in the hundreds, not thousands.
3.3 NIM can be extremely fast on the right hardware (example: DeepSeek-R1)
NVIDIA’s blog says DeepSeek-R1 NIM microservice can run on an HGX H200 system (8× H200) “at up to 3,872 tokens per second.”
Again, this is a system-level number (and depends heavily on batching/concurrency); you should treat it as “upper bound / throughput class” until you measure per-request TTFT/ITL in your own harness.
3.4 Pricing / availability reality
build.nvidia.com advertises “Free serverless APIs for development” (so: great for your “promo/free” ingestion bucket).
NVIDIA forum staff: model rate limits vary and are not published; you can see your max rate limit in the UI.
NVIDIA docs: downloadable NIM is free for research/dev/testing; production requires NVIDIA AI Enterprise starting at $4500 per GPU per year (or “~$1 per GPU per hour” in cloud).
Router implication: treat NIM as two categories of offers:
NIM Serverless (build.nvidia.com): “volatile free/dev” plan; unknown limits; high variance; use telemetry gating.
NIM Self-host: a selfhost offer with cost derived from GPU rentals + measured performance (no per-token billing). 4) Morph and “apply” competitors: they are not general LLMs; they are execution layers
4.1 What Morph actually is
Morph’s OpenRouter page describes it as a specialized code-patching/apply model:
“high-accuracy apply model” ~4,500 tokens/sec with 98% accuracy
“fastest apply model” ~10,500 tokens/sec with 96% accuracy
requires a strict prompt format (<instruction>…</instruction><code>…</code><update>…</update>)
shows token pricing (e.g. $0.80/M input, $1.20/M output for v3 fast).
Fly.io’s writeup repeats:
Apply API processes over 4,500 tokens/sec
~98% accuracy in ~6 seconds per file
and compares to slower/brittle search-replace approaches.
AWS case study claims:
Morph achieved over 10,000 tokens/sec per request
“15,000-token multifile refactor in under 400 ms”
single-file edits under 1 second.
4.2 Competitor: Relace “Apply 3”
OpenRouter’s Relace page: “apply updates … at 10,000 tokens/sec on average” and similar prompt format requirement.
Relace’s own engineering blog explains how they push speed (FP8 conversion + speculative decoding discussion).

Router implication: Morph/Relace are “fast apply” stages that:

should NOT compete head-to-head with Claude/GPT for reasoning
should be routed for a different role (apply/merge/patch)
reduce overall cost/time by letting a strong model output small edit snippets while apply model does the expensive merging quickly 5) Where these fit in your router: the honest take
A) Cerebras = “ultra-fast general generation” offers
Use for:
fast scaffolding (generate code quickly)
interactive coding where you want low ITL / high output speed
agentic workflows that do many calls and benefit from low latency
Risks you must model:
queue time / utilization and burst/RPS causing 429s (they explicitly warn about this).
subscriptions are daily-capped (24M/day, 120M/day) — if you hit the cap you hard-fail until reset.
Catalog design: Cerebras offers should include:
tokensPerDayCap, tpmCap, rpmCap, rpsCap
queueTime_p95 (from telemetry; because it matters a lot)
volatility for preview models
B) NVIDIA NIM = “your self-host acceleration layer + free dev endpoints”
Use for:
deploying mid/high-tier open models with better throughput/ITL than stock deployments
“burst capacity” on GPU rentals (H200/B200 etc.)
dev/test usage via free serverless endpoints
Risks you must model:
build.nvidia.com limits are opaque and variable (don’t route critical traffic there unless you’ve measured).
production economics can include AI Enterprise licensing (irrelevant for hobby; very relevant for enterprise).
Step 3.5 Flash specifically: treat it as a “fast-ish reasoning MoE model” with throughput on the order of 100–300 tok/s (peak 350 in coding) — good, but not in the Cerebras/Morph class.
C) Morph / Relace = “Apply stage” offers
Use for:
file edit / code merge / patch application
making any coding agent feel “instant” by eliminating full-file rewrites
Risks you must model:
strict prompt formatting requirements (hard constraint)
quality is “merge correctness”, not reasoning 6) Update your router: add “micro-roles” and a 2-stage coding DAG
This is the architectural move that actually makes these providers matter.
6.1 Add these roles to your role taxonomy
code_reasoner (high quality)
code_patch_generator (outputs edit snippet / structured patch)
code_apply_patch (Morph/Relace)
code_scaffold_fast (Cerebras / fast models)
code_small_transform (small fast models; also apply-models can serve)
6.2 Coding-agent DAG (how fast apply fits)
┌─────────────────────┐
│ code_reasoner │ (Claude/GPT/etc)
│ decides intent │
└─────────┬───────────┘
│ outputs small "edit snippet"
▼
┌─────────────────────┐
│ code_apply_patch │ (Morph/Relace)
│ merges into files │
└─────────┬───────────┘
│
▼
┌─────────────────────┐
│ run tests / lint │
└─────────┬───────────┘
│ fail => escalate
▼
┌─────────────────────┐
│ code_reasoner (2nd) │
└─────────────────────┘
This is why Morph/Relace “fit”: they remove full-file regeneration from your loop and cut time/cost massively (and the vendor claims are backed by at least one AWS case study). 7) What changes in your indices (specific, implementable)
7.1 Speed index: add TTFT + ITL explicitly
Use NVIDIA’s metric definitions as your standard.
For each offer+role you store:

ttft_p95_ms
itl_p95_ms
tps_stream_p50 (derived from ITL or measured)
queue_ms_p95 (important for Cerebras Code during peak)
Then role-dependent speed score:
For interactive tasks:
speed = 0.5*ttft_p95 + 0.5*(expected_out_tokens \* itl_p95)
For bulk output tasks:
speed = ttft_p95 + expected_out_tokens / tps_stream_p50
For apply_patch tasks:
use end-to-end ms/file (don’t pretend it’s like chat):
speed = p95_apply_ms_per_file
(you’ll measure; vendor claims are guidance).
7.2 Cost index: treat each provider’s metering honestly
Cerebras pay-per-token: straightforward (they publish per-token pricing for models like Llama 3.1 8B).
Cerebras Code Pro/Max: daily bucket (24M/day, 120M/day) + TPM/RPM caps.
Model as daily_quota_bucket not “monthly tokens”.
NIM serverless dev: treat as volatile_free with unknown limits; rely on telemetry.
NIM self-host: cost = GPU rental $/hr ÷ realized throughput × concurrency efficiency.
Morph/Relace: pay-per-token (OpenRouter pages show prices) and cheap relative to frontier.
7.3 Quality index: role-specific quality types
You need separate quality dimensions:
reasoning_quality
code_generation_quality
apply_merge_accuracy
Morph/Relace quality is “merge correctness”; treat it as its own axis for code_apply_patch role. (OpenRouter literally advertises 96–98% accuracy; you should still validate with your own tests.) 8) How to ingest/scrape them into your offer catalog (practical)
Cerebras
Best sources:
inference-docs.cerebras.ai model pages contain speed, pricing, rate limits in structured HTML (easy scrape).
Support FAQ contains plan limits, plus queue-time and burst/429 guidance.
Pricing page for plan tiers + “preview discontinuation” warning.
Blogs for special models (e.g. gpt-oss-120B speed and price).
NVIDIA NIM
Best sources:
NIM microservices page for baseline performance examples (throughput/ITL).
build.nvidia.com model cards for each model’s characteristics (Step 3.5 throughput).
NIM docs for licensing/pricing in production and dev/test.
NVIDIA forums for “limits not published / rate limits vary”.
Morph / Relace
Best sources:
OpenRouter model pages already expose:
prompt format constraints
pricing
claimed tokens/sec
Morph’s AWS case study for high-cred “real world” performance claims.
Relace engineering blog for technical background (optional). 9) Net recommendation (how to actually route with these)
Use Cerebras when:
role is code_scaffold_fast / code_simple / “bulk code output”
you’re under daily token cap and queue time is acceptable
you want cheap token rates for specific models (e.g. Llama 3.1 8B pricing)
Use NIM when:
you can self-host on rentals and want predictable throughput
you want to deploy specific models (including Step 3.5 Flash) and control the stack
you need large-concurrency throughput at good ITL (NIM ON example)
Use Morph/Relace when:
your agent produces edit snippets and you need a fast, correct merge step
you want to make expensive reasoning models “cheap” by shrinking their output
you can enforce the required prompt format (hard constraint)
If you want, I’ll fold this back into your unified PRD/ALD/ADR set as a “Speed Stack” addendum
Specifically:
new roles (apply_patch, scaffold_fast)
new offer fields (TTFT/ITL/queue, bucket caps)
new ADR: “Split coding into Reason → Apply DAG”
ingestion adapters for Cerebras docs + NVIDIA model cards + OpenRouter apply models
Say the word and I’ll output the updated unified doc sections cleanly (diff-style so it’s easy to merge).

You said:
yes

ChatGPT said:

Thought for 12m 23s

Answer now
Below is a merge-ready addendum that plugs Cerebras (Inference + Code subscriptions), NVIDIA NIM (serverless + self-host), Step 3.5 Flash, DeepSeek‑R1 NIM, and fast “apply/patch” models (Morph/Relace) into your unified PRD + phased WBS/DAG + Technical ALD + ADR docket.
I’m going to be blunt about the “3000+ tok/s” claims: they can be real, but they’re often system throughput under concurrency, not “what a single user sees.” NVIDIA’s own benchmarking docs make this distinction explicit (TTFT, ITL, throughput).

A. What changes in the system

1. Add a “Speed Stack” class of offers
   These providers/models are valuable primarily because they optimize TTFT/ITL and throughput, not necessarily peak reasoning.
   Cerebras Inference: e.g., Llama 3.1 8B listed at ~2200 tokens/sec and $0.10/M input/output.
   Cerebras Code subscription: daily token caps + TPM/RPM caps (Code Max: 120M tokens/day, 1.5M TPM, 120 RPM).
   NVIDIA NIM: a deployment/optimization layer; NVIDIA publishes examples like 1201 tokens/s throughput and ITL 32ms (Llama 3.1 8B instruct, 1× H100 SXM, 200 concurrent requests) with NIM ON.
   Step 3.5 Flash (on NVIDIA): advertised at 100–300 tok/s, peak 350 tok/s for single-stream coding tasks.
   DeepSeek‑R1 NIM: NVIDIA claims up to 3872 tokens/sec on a single HGX H200 system.
2. Add an “Apply/Patch stage” class of roles and offers
   Morph/Relace are not general reasoning models — they are file merge / patch-application engines that can run at ~10k tok/s and require a strict prompt structure.
   Morph “fast apply”: ~10,500 tok/s, ~96% accuracy, strict <instruction><code><update> prompt format.
   AWS case study for Morph: “over 10,000 tokens/sec per request” and “15,000-token multifile refactor under 400ms.”
   Relace Apply 3: “apply updates… at 10,000 tokens/sec on average” and similar apply-focused semantics.
   B. PRD patch
   B1) Add to PRD “Optimization Axes” — Speed definition (replace current Speed section)
   CHANGE: Speed Index must be profile-based (TTFT + ITL + throughput), not single ‘toks/sec’.
   Why: NVIDIA’s benchmarking guidance separates TTFT and inter-token latency (ITL/TPOT) and treats throughput as a distinct measure.

Replace Speed Index definition with:
Speed Profile (per offer, per role):
ttft_p50, ttft_p95
itl_p50, itl_p95 (aka time-per-output-token / TPOT)
tps_stream_p50/p95 (derived or measured)
throughput_tokens_s@concurrency (system throughput under a reference concurrency)
queue_ms_p95 (important for subscription services that queue during utilization spikes)
Role-specific speed objective:
Interactive chat/edit:
speed = ttft_p95 + (E[out_tokens] \* itl_p95) + queue_ms_p95
Bulk generation:
speed = ttft_p95 + (E[out_tokens] / tps_stream_p50) + queue_ms_p95
Apply/patch:
speed = apply_ms_p95_per_file (or per N tokens)
B2) Add to PRD “Roles” — new micro-roles
ADD: roles
code_reasoner (deep planning, debugging, architecture)
code_patch_generator (outputs minimal edit snippet / patch instructions)
code_apply_patch (Morph/Relace-style file merge/apply)
code_scaffold_fast (high-throughput code drafting)
code_small_transform (small edits, formatting, rename, docstring injection)
Hard constraints per role (examples):
code_apply_patch:
must support apply prompt format (<instruction><code><update> style)
must support large file contexts (Morph/Relace have large contexts; Relace lists 256k)
code_scaffold_fast:
prefers offers with high tps_stream and low ITL; quality threshold lower than code_reasoner
B3) Add to PRD “Provider classes”
ADD: Provider/Offer classes
Ultra-fast token metered (Cerebras Inference: published tok/s and token pricing)
Ultra-fast daily bucket subscription (Cerebras Code: RPM/TPM/tokens/day caps)
Optimized self-host stack (NVIDIA NIM containers; cost derived from GPU rent + throughput)
Serverless dev endpoints / volatile free (build.nvidia.com: “Free serverless APIs for development”, but limits not published and vary per model)
Apply/Patch specialist (Morph/Relace: prompt-format constrained, very high tok/s)
C. Phased WBS + DAG patch
C1) Add Phase: “Speed Stack integration” (between Telemetry and Router Core)
Phase X — Speed Stack Integration (Cerebras + NIM + Apply models)
Deliverables
Cerebras adapters:
Inference model/pricing ingestion (token metered)
Code plan ingestion (daily caps, RPM/TPM)
NVIDIA adapters:
NIM serverless (build.nvidia.com) as volatile_free offers
NIM self-host offers (cost from compute)
Step 3.5 Flash offer ingestion (known throughput band 100–300 tok/s)
Apply model adapters:
Morph / Relace ingestion (pricing + prompt constraints)
Telemetry upgrades:
capture TTFT + ITL + queue time in logs (NVIDIA defines TTFT/ITL as core metrics)
New role DAG execution:
code_patch_generator -> code_apply_patch -> validate pipeline
DAG (new edges)
Offer Ingestion ─────────┐
Telemetry Upgrade ───────┼─> Speed Profile Snapshot ─┐
Plan/Budget Engine ──────┘ │
v
Router Core (Pareto)
|
v
Patch DAG Executor (optional for agents)
D. Technical ALD patch
D1) Offer schema delta (add these fields)
ADD to Offer
speedProfileHints (vendor claims, used as priors)
vendor_tps_stream
vendor_throughput_tokens_s_at_concurrency
vendor_itl_ms / vendor_ttft_ms (if available)
measuredSpeedProfile (from telemetry)
ttft_p95_ms, itl_p95_ms, tps_stream_p50, queue_p95_ms
quotaModel (required for Cerebras Code)
tokensPerDayCap, tokensPerMinCap, requestsPerMinCap
volatilityRisk (required for preview/serverless dev endpoints)
because build.nvidia.com “free serverless APIs for development” can have changing limits
promptContract (required for apply models)
contractType: apply_v1
requiredFormat: "<instruction><code><update>"
maxContextTokens (Relace lists 256k context on OpenRouter)
D2) Economics Engine delta
D2.1 Cerebras Code = daily quota bucket (not monthly bucket)
Cerebras Code Pro/Max have explicit tokens/day and TPM/RPM caps.
Plan type:

daily_quota_bucket
Effective cost for daily quota bucket
You don’t compute $/token from “monthly tokens”.
You compute pacing and shadow from daily caps:
remaining_today = tokensPerDayCap - tokensUsedToday
expected_remaining_today = tokensPerDayCap \* remaining_day_fraction

day*shadow = 1 / max(remaining_today / expected_remaining_today, ε)
effective_cost = base_cost * day_shadow _ monthly_budget_shadow
Also:
Add rate-limit penalty if you’re near TPM/RPM; Cerebras explicitly lists those caps and notes limits can change.
D2.2 NVIDIA build.nvidia.com serverless = volatile free plan
It’s advertised as “Free serverless APIs for development.”
NVIDIA staff explicitly says “rate limits vary” and “we do not publish those.”
So treat:
plan.type = volatile_free
cost floor + volatility penalty + observed throttling penalty:
effective_cost = floor_cost + volatility_penalty + throttle_penalty
Throttle penalty increases as you see 429/5xx.
D2.3 NIM self-host = compute-metered
Use measured throughput and rental cost:
effective_$per_token = ($/hour) / (tokens_per_hour_realized)
Where:
tokens_per_hour_realized = measured aggregate tokens/sec at your reference concurrency × 3600.
NIM ON vs OFF example provides a sanity check that throughput can nearly 2× and ITL improves in some configs.
D3) Telemetry pipeline delta: add TTFT/ITL capture
ADD: telemetry event fields:
ttft_ms
itl_ms_avg (or distribution)
stream_tokens_per_sec
queue_wait_ms (if detectable)
concurrency_at_time (if you control gateway)
NVIDIA’s benchmarking docs strongly emphasize TTFT and ITL as first-class metrics.
ASCII: Telemetry pipeline (updated)
[Gateway Exec] -> [Event Log] -> [Aggregator]
| | |
| | +--> TTFT/ITL/TPS windows
| |
| +--> 429/5xx + queue time inference
|
+--> [Per-role token stats] (verbosity, turns)
D4) Add “Patch DAG Executor” (optional component, but you’ll want it)
Why: Apply models only pay off when your agent doesn’t ask the reasoner model to rewrite entire files.
ASCII: Patch-based coding workflow
┌──────────────────────────┐
│ Role: code_reasoner │ (Claude/GPT/etc)
│ - decide approach │
│ - produce small update │
└─────────────┬────────────┘
│ (edit snippet / patch intent)
▼
┌──────────────────────────┐
│ Role: code_apply_patch │ (Morph/Relace)
│ - merge into file(s) │
│ - returns updated file │
└─────────────┬────────────┘
│
▼
┌──────────────────────────┐
│ Validate (tests/lint) │
└─────────────┬────────────┘
│ fail
▼
┌──────────────────────────┐
│ Escalate: code_reasoner │
└──────────────────────────┘
This is how you exploit 10k tok/s apply throughput without turning the whole system into “apply model roulette.” Morph/Relace are great at merging; they’re not your planner.
E. ADR docket additions (new ADRs)
ADR-008: Replace single “tokens/sec” with TTFT + ITL + throughput profile
Decision: Speed Index uses TTFT and ITL explicitly; throughput is tracked separately.
Rationale: NVIDIA benchmarking guidance treats TTFT and ITL as fundamental metrics, not interchangeable with tokens/sec.
Status: Accepted.
ADR-009: Add Patch/Apply stage as first-class routing role
Decision: Introduce code_apply_patch role for apply-focused models (Morph/Relace).
Rationale: These models require strict prompt contracts and provide specialized merge throughput (~10k tok/s) and should not compete with reasoning models directly.
Status: Accepted.
ADR-010: Model Cerebras Code as a daily-quota bucket plan
Decision: Treat Cerebras Code subscription as daily-cap + TPM/RPM constraints.
Rationale: Code Pro/Max are documented with tokens/day and TPM/RPM caps; monthly token assumptions are wrong.
Status: Accepted.
ADR-011: Treat NVIDIA build.nvidia.com as “volatile free” with limits-discovery
Decision: Serverless NIM endpoints are classified as volatile; enforce telemetry-gated canary and dynamic throttling penalties.
Rationale: NVIDIA staff states per-model rate limits vary and are not published; build advertises free serverless APIs for development.
Status: Accepted.
ADR-012: Store vendor speed claims as priors; routing uses measured telemetry
Decision: Vendor-stated tok/s numbers are “speed hints”; router decisions use measured TTFT/ITL/TPS after burn-in.
Rationale: Throughput numbers may be system-level and configuration-dependent (e.g., NIM performance examples include concurrency and hardware).
Status: Accepted.
F. Catalog examples (how these appear as offers)
F1) Cerebras Inference (token metered, ultra-fast)
published ~2200 tok/s and $0.10/M in/out for Llama 3.1 8B.
Offer class: ultra_fast_token_metered
F2) Cerebras Code Max (subscription, daily cap)
Code Max: 120M tokens/day, 1.5M TPM, 120 RPM.
Offer class: ultra_fast_daily_bucket
F3) NVIDIA NIM serverless (volatile free)
build: “Free serverless APIs for development,” but limits vary and aren’t published.
Offer class: volatile_free
F4) Step 3.5 Flash
100–300 tok/s, peak 350 for coding tasks.
Offer class: fast_reasoning
F5) DeepSeek‑R1 NIM microservice
up to 3872 tokens/sec on HGX H200 (vendor claim).
Offer class: ultra_fast_system_throughput (must measure per-request TTFT/ITL yourself)
F6) Morph / Relace Apply
Morph: ~10,500 tok/s (fast) and ~4,500 tok/s (high-accuracy large), strict apply prompt contract.
Relace Apply 3: ~10,000 tok/s average.
Offer class: apply_patch
G. Practical routing rules (so this doesn’t become a mess)
Rule 1 — Apply models never enter the same candidate set as reasoners
They are separate roles; otherwise Pareto will do dumb things.
code_reasoner candidate pool: your normal big models.
code_apply_patch candidate pool: Morph/Relace only.
Rule 2 — Cerebras Code daily bucket should be preferred early-day, not late-day
Because tokens/day resets matter more than monthly pacing; you’ll want a per-day shadow.
Rule 3 — NVIDIA serverless endpoints should be canary-only until telemetry stabilizes
Limits vary and aren’t published; treat as volatile with aggressive throttling penalties.
Rule 4 — Step 3.5 Flash is “fast-ish”, not a 3000 tok/s class model
If someone’s telling you “Step 3.5 does 3000 tok/s” they’re mixing categories. The model card itself states 100–300 tok/s typical.
If you want, I can now output a single consolidated “v1.1 Unified Doc” with these patches applied inline (instead of patch notes), but the above is already structured so you can merge section-by-section cleanly.

You said:
yes

ChatGPT said:

Thought for 14m 15s

ChatGPT said:
Helios Router v1.1 (Feb 2026)
Unified PRD + Phased WBS/DAG + Technical ALD + ADR Docket
Scope update: Cerebras, NVIDIA NIM (serverless + self-host), Step 3.5 Flash, DeepSeek‑R1 NIM, Morph/Relace Apply

1. PRD
   1.1 Purpose
   Build a model-agnostic routing control plane for coding workloads that selects the best Offer (model+provider+plan+region) under hard constraints, then optimizes across Speed, Cost, and Quality. Key update in v1.1: incorporate “speed-stack” and “apply/patch” specialist offers that radically change the best architecture for coding agents (especially file editing).
   1.2 Problem statement
   You operate a messy fleet:
   multiple paid subscriptions with unclear “true token coverage”
   metered premium units (Copilot) with model multipliers and 0× models
   rate/plan caps (tokens/day, TPM/RPM, RPS bursts)
   volatile preview/free offers
   self-host rentals that are only “cheap” if throughput is real
   Static “pick a model” logic fails because:
   pricing and availability move
   the same model via different providers/tiers behaves differently
   speed claims are often apples-to-oranges (TTFT vs ITL vs throughput)
   1.3 Scope
   In scope
   Offer-first routing (select provider+model+plan directly)
   unified plan economics:
   PAYG token-metered
   fixed “bucket” subscriptions (learned EUC)
   daily quota buckets (Cerebras Code)
   weighted premium units (Copilot)
   rate-limited prompts (Minimax-style)
   volatile free / promo endpoints (NVIDIA serverless NIM, rotating previews)
   speed index upgraded to TTFT + ITL + throughput profile
   quality index robust to missing benchmark entries
   patch-based coding DAG: Reason → Apply → Validate → Escalate
   Out of scope (v1.1)
   fully learned routing policy (bandits/RL) — keep Pareto + lexicographic
   automated benchmark OCR / screenshot extraction (you said you’ll enter manually)
   1.4 Ground-truth constraints and assumptions
   Budget envelope configurable; default:
   Variable spend cap: $600/month (PAYG + overages + GPU rentals)
   Fixed subscriptions: tracked separately (or optionally included if you want a hard total cap)
   Copilot semantics:
   Premium requests are deducted based on model multipliers, and some models (e.g., GPT‑5 mini, GPT‑4.1, GPT‑4o) are “included” and don’t consume premium requests on paid plans.
   GitHub documents that models have premium request multipliers and that multipliers can change.
   1.5 Users / journeys
   Primary user: your internal harness / IDE agent runtime (Codex CLI harness variants).
   Secondary user: you (admin) managing providers, plans, budgets, and incident response.
   Journey A — Route+Execute (hot path)
   client sends (role, messages, hard constraints, optional maxCost)
   router loads snapshots (offers/econ/telemetry/quality)
   hard-filter → Pareto → lexicographic select
   execute selected offer, log metrics
   on failure, follow fallback chain based on error type
   Journey B — Add provider/model
   add adapter config + creds
   ingest offers (inactive/canary)
   collect telemetry + online quality signals
   promote to active once stable
   Journey C — “Speed stack” integration
   ingest ultra-fast offers (Cerebras, NIM)
   ingest apply/patch offers (Morph/Relace)
   enable patch DAG roles and route edits through apply models
   1.6 Functional requirements
   FR-1 Offer-first catalog
   Store routable Offer objects (provider+model+plan+region) instead of “models”.
   Offers must capture:
   capabilities (tools/json/vision/context)
   limits (RPM/TPM/RPS/tokens/day)
   pricing semantics (token / unit / bucket / compute-metered)
   risk/volatility class
   FR-2 Plan/economics engine
   Support plan types:
   payg_token
   fixed_bucket_tokens (Claude Max / Codex / GLM prior; learned EUC)
   daily_quota_bucket (Cerebras Code: tokens/day + TPM/RPM + RPS burst)
   weighted_unit_bucket (Copilot multipliers + included 0× models)
   prompt_rate_limited (Minimax-style)
   volatile_free (NVIDIA serverless NIM “free serverless APIs for development”, rate limits not published/variable)
   compute_metered (NIM self-host on rentals)
   FR-3 Speed index uses TTFT+ITL
   Speed is computed from measured latency profile; vendor “tok/s” claims are priors only.
   NVIDIA defines TTFT and ITL/TPOT and treats them as fundamental metrics.
   FR-4 Quality index stable under missing benchmarks
   normalize per benchmark
   family/global shrinkage imputation for missing
   coverage penalty
   blend with online outcomes as they accumulate
   FR-5 Patch-based coding DAG
   For file edits: separate roles:
   code_reasoner → produces intent + minimal edit snippet
   code_apply_patch → merges snippet into file(s) using apply model
   validate → tests/lint/build
   escalate on failure
   Apply models (Morph/Relace):
   very high apply throughput (10k+ tok/s class) and require strict prompt contracts.
   FR-6 Fallback + circuit breakers
   fallback chain generated per request
   circuit breaker disables flaky offers based on error rate/429 spikes
   1.7 Non-functional requirements
   router decision latency: <5ms p95 (in-memory snapshots)
   deterministic decisions per snapshot version
   clear trace output: why an offer won
   provider outages should degrade gracefully, not cascade
   1.8 Success metrics (KPIs)
   Cost: stay within variable cap; reduce overages
   Speed: reduce p95 “time-to-usable-answer” per role
   Quality: reduce escalation rate (how often you rerun on stronger model)
   Stability: reduce 429/5xx-induced retries and tool/schema failures
2. Technical model (indices + routing policy)
   2.1 Offer = unit of routing (non-negotiable)
   You route to:
   offerId = provider + model + plan + region (+ mode)
   This is required because:
   Copilot uses multipliers and included 0× models
   Cerebras Code has daily caps + TPM/RPM + RPS burst behavior
   NVIDIA serverless NIM limits vary and aren’t published
   2.2 Speed index (v1.1)
   Store a speed profile, not one number. Per offer+role, maintain:
   ttft*p95_ms
   itl_p95_ms (aka TPOT)
   tps_stream_p50
   queue_p95_ms (important for queued services)
   optional tps_agg@concurrency (system throughput)
   Role-specific speed score: Interactive:
   speed = queue_p95_ms + ttft_p95_ms + E[out_tokens]*itl_p95_ms
   Bulk:
   speed = queue_p95_ms + ttft_p95_ms + E[out_tokens]/tps_stream_p50
   Apply/Patch:
   speed = apply_ms_p95_per_file
   Why this matters:
   NIM performance numbers often depend on concurrency; NVIDIA shows throughput and ITL under 200 concurrent requests on H100.
   Step 3.5 Flash is “fast-ish” (~100–300 tok/s, peak 350), not a 3000 tok/s class model.
   2.3 Cost index (v1.1)
   You compute effective_cost_usd(request, offer) using plan semantics + shadow pricing.
   A) PAYG token-metered
   cost = Tin*p_in + Tout*p_out Example: Cerebras publishes low token pricing for specific models (e.g., Llama 3.1 8B at $0.10/M in/out, with ~2200 tok/s listed on their pricing page).
   B) Fixed bucket tokens (Claude/Codex/GLM-style)
   Compute EUC (effective unit cost) and update from logs:
   EUC ≈ monthly_fee / tokens_covered_est
   cost = EUC * (Tin+Tout)
   Tokens_covered_est is a learned latent variable (EWMA) because “bucket size” is rarely stable in reality.
   C) Daily quota bucket (Cerebras Code)
   Cerebras Code Pro/Max: explicit tokens/day + TPM/RPM and RPS burst constraints. Shadow must be daily, not monthly:
   day_shadow = 1 / max(remaining_today / expected_remaining_today, ε)
   effective_cost = base_cost * day*shadow * budget*shadow
   Also add rate-limit penalty if close to TPM/RPM/RPS caps.
   D) Weighted unit bucket (Copilot premium requests w/ multipliers + 0×)
   GitHub docs: models have premium request multipliers; some models are “included” on paid plans and don’t consume premium requests. Model it as:
   units consumed per request = multiplier(model, feature)
   overage price per unit is configurable (GitHub documents “premium requests,” you parameterize cost rules)
   Effective cost per request:
   implied_cost = unit_overage_usd * units*consumed
   unit_shadow = 1 / max(remaining_units / expected_remaining_units, ε)
   effective_cost = implied_cost * unit*shadow * budget*shadow
   For 0× models:
   monetary cost is 0, but you still apply:
   volatility/availability risk (they can be reclassified)
   quality thresholds
   mild floor cost only for tie-breaking (optional)
   E) Volatile free (NVIDIA serverless NIM)
   NVIDIA build.nvidia.com: “Free serverless APIs for development.”
   NVIDIA staff: per-model rate limits vary and aren’t published. So:
   set cost near-zero
   but apply strong volatility penalty and throttle penalty from observed 429/queue
   F) Compute-metered (self-host NIM)
   Compute:
   $/token = ($/hour) / (measured_tokens_per_hour_at_ref_concurrency)
   NVIDIA claims NIM can materially improve throughput and ITL in published examples (NIM ON vs OFF).
   2.4 Quality index (v1.1)
   You will have spotty benchmark coverage. The system must not collapse.
   Offline quality (benchmarks you input)
   Normalize per benchmark to z-scores.
   Impute missing benchmark values via shrinkage:
   z_hat = λ * mean*z(family, b) + (1-λ) * mean*z(global, b)
   Apply coverage penalty so sparse models don’t float to the top by luck:
   offline_adj = offline * (0.6 + 0.4*coverage)
   Online quality (your reality)
   Per role:
   coding: test pass rate, lint/build success, escalation rate, tool/json adherence
   apply role: merge correctness / patch success rate
   Blend:
   quality = (1-ρ(n))*sigmoid(offline_adj) + ρ(n)\*online_quality
   ρ(n)=n/(n+k)
   2.5 Router policy
   hard filter (capabilities, context, maxCost, minQuality, compliance)
   compute objective vector per offer:
   minimize speed_score
   minimize effective_cost_usd
   maximize quality_score
   Pareto frontier
   lexicographic selection (role-specific order)
   execute + log + fallback chain
3. System design (ALD)
   3.1 High-level architecture
   ┌────────────────────────────┐
   │ Client / IDE / Agent Harness│
   └──────────────┬─────────────┘
   │ (role + msgs + hard/soft)
   ▼
   ┌─────────────────────┐
   │ Router API (hotpath)│
   └───────┬─────────────┘
   │ loads immutable snapshots
   ▼
   ┌─────────────────────────────────────────────┐
   │ Hard Filter -> Score -> Pareto -> LexiPick │
   └───────────────┬─────────────────────────────┘
   │
   ▼
   ┌─────────────────────────┐
   │ Execution Gateway │ (OpenAI-compat shim)
   └───────┬─────────────────┘
   │
   ┌───────────────┼──────────────────────────┐
   ▼ ▼ ▼
   [Provider Adapters] [Self-host/NIM] [Apply/Patch Adapters]
   (OpenRouter, etc.) (GPU rentals) (Morph/Relace)
   3.2 Control plane vs data plane
   Data plane (hot path):
   Router API
   Execution Gateway (your existing harness normalization)
   Minimal fallback engine
   Control plane (slow path jobs):
   Offer Registry
   Plan Registry + Economics Engine
   Telemetry Aggregator
   Quality Engine
   Snapshot Builder
   3.3 Key pipelines
   Pipeline A — Offer ingestion
   Sources:
   provider APIs / docs
   OpenRouter model pages (for apply models)
   GitHub Copilot docs for multipliers + included models (policy baseline)
   Output:
   OfferRegistry + OfferSnapshot
   Pipeline B — Telemetry ingestion (mandatory)
   Per request, log:
   ttft_ms, itl_ms, total_latency_ms
   tokens in/out (or estimate)
   errors (429/5xx/timeout/schema)
   provider/offerId
   role
   queue time if inferable
   NVIDIA’s benchmarking framework treats TTFT/ITL as core metrics.
   Pipeline C — Economics snapshot
   updates plan remaining (premium units remaining, daily tokens remaining, etc.)
   recomputes shadow prices (budget + plan pacing)
   emits EconomicsSnapshot used by router
   3.4 Patch DAG executor (v1.1 add-on component)
   This is how Morph/Relace fit without doing dumb “replace all code with apply model” routing.
   ┌──────────────────────────┐
   │ code_reasoner │ (Claude/GPT/etc)
   │ - plans + writes snippet │
   └─────────────┬────────────┘
   │ edit snippet
   ▼
   ┌──────────────────────────┐
   │ code_apply_patch │ (Morph/Relace)
   │ - merges into file(s) │
   └─────────────┬────────────┘
   │
   ▼
   ┌──────────────────────────┐
   │ validate (tests/lint) │
   └─────────────┬────────────┘
   │ fail → escalate
   ▼
   ┌──────────────────────────┐
   │ code_reasoner (stronger) │
   └──────────────────────────┘
   Morph and Relace are explicitly “apply/patch” models with strict input formats and high apply throughput.
   AWS cites Morph achieving 10k tokens/sec per request and very low latency for large refactors.
   3.5 Provider-specific integration notes (what changes in the catalog)
   Cerebras
   Token-metered inference offers: easy cost modeling and speed priors (pricing pages list tokens/sec + $/M token).
   Cerebras Code subscription offers: must be modeled as daily_quota_bucket (24M/day Pro, 120M/day Max; plus TPM/RPM and RPS burst).
   Preview models can be discontinued (volatility flag).
   GPT‑OSS‑120B on Cerebras: “up to 3,000 tokens/sec” and published $/M in/out.
   NVIDIA NIM
   Two offer classes:
   Serverless build.nvidia.com offers: “Free serverless APIs for development” but limits vary and aren’t published → volatile_free + telemetry gating.
   Self-host NIM offers: compute-metered; cost derived from GPU rentals and measured throughput. NIM performance examples include throughput and ITL values.
   Step 3.5 Flash:
   throughput 100–300 tok/s (peak 350); treat as “fast-ish” not ultra-fast.
   DeepSeek‑R1 NIM:
   NVIDIA claims up to 3,872 tokens/sec on HGX H200; treat as system-level prior until you measure TTFT/ITL in your own harness.
   Morph / Relace
   Add as apply_patch offers only; they should not enter general reasoning candidate sets.
   3.6 Example catalog (trimmed, offer-first)
   Plans
   plans:

- planId: copilot-pro-student
  type: weighted_unit_bucket
  premiumUnitsIncluded: 300
  unitOverageUsd: 0.04 # configurable
  modelMultipliersSource: github_docs

- planId: cerebras-code-max
  type: daily_quota_bucket
  tokensPerDayCap: 120_000_000
  tpmCap: 1_500_000
  rpmCap: 120

- planId: nvidia-nim-serverless
  type: volatile_free

- planId: nvidia-nim-selfhost
  type: compute_metered
  costModel: gpu_hour_div_throughput
  Offers
  offers:
- offerId: copilot:gpt-5-mini:chat
  provider: copilot
  modelId: gpt-5-mini
  planId: copilot-pro-student
  unitMultiplier: 0.0
  caps: { tools: true, json: true, maxContext: 128000 }

- offerId: cerebras:code-max:qwen3-coder
  provider: cerebras
  modelId: qwen3-coder
  planId: cerebras-code-max
  caps: { tools: true, json: true, maxContext: 128000 }

- offerId: nvidia:build:step-3.5-flash
  provider: nvidia-build
  modelId: step-3.5-flash
  planId: nvidia-nim-serverless
  caps: { tools: true, json: true, maxContext: 256000 }

- offerId: openrouter:morph-v3-fast:apply
  provider: openrouter
  modelId: morph-v3-fast
  planId: openrouter-payg
  roleOnly: code_apply_patch
  promptContract: apply_v1
  (You’ll generate dozens/hundreds of offers in practice; this is just to show structure.)

4. Phased WBS + DAG (v1.1)
   Phase 0 — Foundations
   WBS
   P0.1 Canonical schemas (Offer/Plan/Snapshots)
   P0.2 Offer Registry + versioned snapshots
   P0.3 Execution gateway contract (OpenAI-compat normalization)
   P0.4 Audit logging + trace IDs
   DAG
   Schemas -> Registry -> Snapshot Builder
   Schemas -> Gateway Contract -> Router API
   Phase 1 — Economics Engine (plans + budget)
   WBS
   P1.1 Plan types: payg_token, fixed_bucket_tokens, daily_quota_bucket, weighted_unit_bucket, prompt_rate_limited, volatile_free, compute_metered
   P1.2 Budget pacing shadow (global)
   P1.3 Plan pacing shadows (per-plan)
   P1.4 EconomicsSnapshot builder
   DAG
   Plan Registry -> Plan Calculators -> Shadow Prices -> EconomicsSnapshot
   Budget Tracker ----------------------^
   Phase 2 — Telemetry + Speed Profiles
   WBS
   P2.1 Emit TTFT/ITL metrics in gateway logs
   P2.2 Aggregator computes p50/p95 and queue inference
   P2.3 Role-based verbosity stats (E[out_tokens])
   P2.4 TelemetrySnapshot builder
   DAG
   Gateway Logs -> Aggregator -> Speed Profiles -> TelemetrySnapshot
   Phase 3 — Quality Engine (sparse benchmarks + online)
   WBS
   P3.1 Benchmark matrix ingest (manual values)
   P3.2 Normalize per benchmark
   P3.3 Family/global shrinkage imputation
   P3.4 Coverage penalty + confidence
   P3.5 Online outcomes (tests pass, escalation, adherence)
   P3.6 QualitySnapshot builder
   DAG
   Benchmarks -> Normalize -> Impute -> QualitySnapshot
   Online Eval ------------------------^
   Phase 4 — Router Core
   WBS
   P4.1 Hard constraint engine
   P4.2 Pareto frontier implementation
   P4.3 Lexicographic selector (role-specific)
   P4.4 Fallback chains + circuit breakers
   P4.5 Route trace output + explainability fields
   DAG
   (OfferSnapshot + EconomicsSnapshot + TelemetrySnapshot + QualitySnapshot)
   -> Filter -> Score -> Pareto -> Pick -> Execute
   Phase 5 — Speed Stack Integration (v1.1 add)
   WBS
   P5.1 Cerebras adapters:
   token-metered offers (pricing/speed priors)
   Code Pro/Max as daily_quota_bucket
   P5.2 NVIDIA adapters:
   build.nvidia.com serverless offers as volatile_free
   NIM self-host offer type
   P5.3 Apply model adapters:
   Morph/Relace apply offers (prompt contract enforcement)
   P5.4 Telemetry gating rules for volatile_free offers
   DAG
   Adapters -> OfferSnapshot
   Telemetry -> Gating -> Router Candidate Sets
   Phase 6 — Patch DAG Executor
   WBS
   P6.1 Implement reason→apply→validate pipeline
   P6.2 Add role policies for apply_patch
   P6.3 Safety checks (prevent file deletion, patch sanity)
   P6.4 Escalation and rollback behaviors
   DAG
   code_reasoner -> code_apply_patch -> validate -> (pass|escalate)
5. ADR docket (v1.1)
   ADR-001 Offer-first routing
   Decision: Route to offerId (provider+model+plan), not model.
   Why: plan semantics and limits materially change feasibility and economics (Copilot multipliers, Cerebras daily caps, NVIDIA unpublished limits).
   Status: Accepted.
   ADR-002 Pareto frontier + lexicographic tie-break
   Decision: Hard constraints → Pareto prune → role-specific lexicographic selection.
   Why: avoids brittle scalar weights; keeps behavior stable.
   Status: Accepted.
   ADR-003 Copilot = weighted unit bucket + 0× included models
   Decision: Treat Copilot premium usage as multiplier-weighted units; included models consume 0 units on paid plans per GitHub docs.
   Status: Accepted.
   ADR-004 Speed profile uses TTFT+ITL (not “tok/s”)
   Decision: Store TTFT/ITL and separate system throughput; compute role-specific speed.
   Why: TTFT and ITL are fundamental and not interchangeable with throughput.
   Status: Accepted.
   ADR-005 Cerebras Code modeled as daily_quota_bucket
   Decision: Use tokens/day + TPM/RPM + RPS burst limits; daily shadow pacing.
   Status: Accepted.
   ADR-006 NVIDIA build.nvidia.com serverless classified as volatile_free
   Decision: Cost-near-zero but telemetry-gated; strong throttle/queue penalties.
   Why: “Free serverless APIs for development” + limits vary and aren’t published.
   Status: Accepted.
   ADR-007 Apply/Patch models are separate role + DAG stage
   Decision: Morph/Relace are only candidates for code_apply_patch and are used via Reason→Apply pipeline.
   Why: they require strict prompt contracts and are specialized for merging edits at very high throughput.
   Status: Accepted.
   ADR-008 Vendor speed claims are priors; measured telemetry wins
   Decision: tok/s marketing numbers seed priors; routing uses observed TTFT/ITL and failure rates.
   Why: many speed numbers are hardware/concurrency dependent (see NIM performance examples).
   Status: Accepted.
6. “Tell it like it is” notes (so you don’t build the wrong thing)
   Step 3.5 Flash is not a 3000 tok/s model. Its own model card pegs it in the ~100–300 tok/s range (peak 350).
   NIM “tokens/sec” claims are often throughput under concurrency. You must track TTFT/ITL and measure in your harness, or you’ll misroute.
   Cerebras Code will 429 you if you burst. Their FAQ explicitly calls out RPS burst behavior and that limits can change.
   Morph/Relace only pay off if you stop rewriting full files with a reasoner model. If you don’t implement the patch DAG, you’re leaving most of the value on the table.
   If you want the next concrete artifact, I can output a single JSON Schema set (Offer/Plan/Snapshots/TelemetryEvent) plus a reference implementation pseudocode for:
   the Copilot weighted-unit cost calculator
   the Cerebras daily quota shadow
   Pareto frontier pruning (O(N²) baseline + faster option)
