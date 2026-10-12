# The gateway layer — one controlled seam for agent traffic

**Load this when:** many clients meet many servers, tool access needs to differ per caller,
somebody has asked who is allowed to call what and you cannot answer from one place, or an
agent calls another **on someone's behalf** and the callee has to know for whom.

**Spec pinned:** agentgateway `1.4.x` from `agentgateway.dev/docs/standalone/latest` · read 2026-08-13

**Delegation pinned:** RFC 8693 §4.1–4.2, RFC 8725 §3.11, RFC 8785; worked example Fabric
`fabric-delegation/0.1` (`passioncode-ai/fabric-agent-contract@8e49fbd`, ADR-0144 at
`passioncode-ai/fabric@812876cf`) · read 2026-10-11

Linux Foundation, Apache-2.0, written in Rust.

This file is **vendor-neutral first**: what a gateway for agent traffic must do, then
agentgateway as a named reference implementation. Swap the implementation and the first half
still holds.

## Contents

- Why an API gateway is not enough
- What a gateway must do
- Federation and the name-collision problem
- Where authorization belongs
- Delegation — who is acting, and for whom
- agentgateway, concretely
- Traps

## Why an API gateway is not enough

A conventional gateway assumes stateless request/response. Agent traffic breaks four of its
assumptions at once, and each break is a feature you would otherwise build by hand:

| Assumption | What agent traffic does |
|---|---|
| one request, one upstream | **multiplexes** across several tool servers and merges the result into one surface |
| the server answers when asked | servers **initiate** events — SSE streams, change notifications |
| the protocol is fixed | MCP and A2A **revise**, so the hop has to negotiate versions rather than pass bytes |
| authorization is per route | authorization is **per tool and per client**, inside one route |

There is also a threat class with no HTTP analogue: **tool tampering, tool shadowing, and
rug-pull** — where a server's advertised tools change after approval, or one server's tool
name shadows another's. A proxy that only forwards cannot see any of it happen.

## What a gateway must do

Independent of product:

1. **Terminate and re-establish the protocol**, not tunnel it — otherwise none of the rest is
   possible.
2. **Federate many servers behind one endpoint**, with a deliberate answer to name
   collisions.
3. **Carry server-initiated events** across the hop, including reconnects, without silently
   dropping subscriptions.
4. **Authorize per tool and per caller**, not per route.
5. **Pin and negotiate protocol revisions**, so one server upgrading does not break every
   client at once.
6. **Detect change in the advertised surface.** A tool set that changes after approval is the
   rug-pull; somebody has to notice.
7. **Emit one audit trail** across every hop, with the identity that made the call attached
   to it.
8. **Route model traffic too**, where the same seam fronts LLM providers — otherwise you run
   two proxies and two policies.

**The reason to want one at all:** without it, each of these lands in every client
separately, and the security answer becomes "it depends which client".

## Federation and the name-collision problem

Two servers, both exposing `search`. The model sees one name and the router picks by load
order — which is a coin flip that looks like a bug in the model.

The general answer is **namespacing at the federation point**, and the general trap is
**doing it inconsistently**, because tool names are what the model learned. A name that
changes between sessions invalidates every prompt, cache and eval that referenced it.

agentgateway's shape, as a concrete instance: multiple **targets** combine into one backend —
"Virtual MCP" — with tool names prefixed by target name (`time_get_current_time`,
`everything_echo`), controlled by `prefixMode`:

| `prefixMode` | Behaviour |
|---|---|
| `conditional` *(default)* | prefix only when the backend has more than one target |
| `always` | prefix even with a single target |
| `never` | never prefix — names must already be unique, or initialization fails |

**`conditional` is a friendly default and a latent break.** Add a second target and every
tool name in the first one changes. If anything persists tool names — a prompt, a cached
plan, an eval fixture — choose `always` up front and pay the ugliness once.

```yaml
backends:
  - mcp:
      targets:
        - name: time
          stdio:
            cmd: uvx
            args: ["--with", "mcp<2", "mcp-server-time"]
        - name: everything
          stdio:
            cmd: npx
            args: ["@modelcontextprotocol/server-everything"]
```

## Where authorization belongs

**At the gateway, and again at each hop.** A gateway is the right place to express "this
client may call these tools" because it is the one place that sees every call. It is the
wrong place to make it the *only* check, because a server reachable by any other path is
unprotected.

Two rules that survive any product choice:

- **Policy per hop, not only at the entrance.** A chain of agents passes context onward, and
  authority does not automatically travel with it.
- **The gateway sees the calls, not the intent.** It can enforce that a tool may be called;
  it cannot tell whether the model was manipulated into calling it. Content inspection is
  probabilistic — anything consequential needs a deterministic limit or a human. See
  `agent-orchestrator/references/governance.md`.

## Delegation — who is acting, and for whom

"Authority does not automatically travel" is the problem; this is the shape that carries it.
Without it, every callee sees one of two wrong things: **a shared token** (it cannot tell
callers apart, so no limit holds per caller) or **the callee's own host credential borrowed
by the caller** (a confused deputy with that service's full power). Neither says on whose
behalf the work runs.

**First, whether a token is needed at all — trust by machine.** Proof is owed at a
boundary, and the operator's own machine is not one. Requiring a token, an approval and a
grant record for every local call buys ceremony, and nobody can attribute a cost to it.

| Tier | Where the call comes from | What it needs |
|---|---|---|
| T0 | the operator's own machine | the operator's instruction is the authority: no delegation token, no approval, no grant record |
| T1 | another machine of the operator's, once it is enrolled in the operator's agent network | the same as T0 |
| T2 | another person's machine, or any outside caller | everything below: a share grant with limits, an expiry and a payer, a token per call, an approval per effect |

Two rules hold on **every** tier:
- **Money limits and human gates.** Every spend limit (project, estate, each key's
  ceiling) applies, and so does every gate a person holds: sign-in, consent, payment.
- **No borrowed keys.** An agent never spends another agent's key. It calls that agent's
  capability, so the owner's wallet and limits apply.

On a T0/T1 path the token below is optional and used for attribution only. A service
that takes calls across the machine boundary, or from outside people, requires it.
Enrolment is what moves a machine from T2 to T1. A machine is never trusted because it
is on the same network.

**The token.** One short signed document per call path, in the shape of OAuth 2.0 Token
Exchange (RFC 8693):

| Claim | Carries | The rule that makes it work |
|---|---|---|
| `sub` | the **person** the work is for | always a person — even when the grant was given to an agent, `sub` is whoever gave it; the agents are the next claim |
| `act` | the **actor chain** (RFC 8693 §4.1) | the agent calling now outermost, earlier actors nested inside; cap the depth (Fabric: 4) |
| `aud` | **one** callee | a string, never an array: a token good at two callees is a token one of them can replay at the other |
| `scope` | the callee's capability names (§4.2) | whole names, space-delimited |
| effect ceiling | the most a call may *do* — read, draft, send, charge, delete, deploy… | external effects are not ordered against each other: a `delete` ceiling admits no `charge` |
| grant reference | the standing grant the call is under | opaque to the callee; it is what usage reports attribute spend by |
| `exp`, `jti` | minutes, not hours (Fabric: at most 600 s) | there is no long-lived token between agents; revoking the grant stops minting at once |

Give the token an explicit `typ` (RFC 8725 §3.11) so it cannot be read as another document
the same key signs.

**One issuer, and the issuer narrows.** A single issuer that holds the operator's consent
mints by token exchange: the caller proves itself and asks for one audience and some
capabilities, and gets a token only inside a live grant. A token for an onward call only
**narrows** its parent — same principal, one more actor, no wider effect, no later expiry,
no more remaining spend. Attenuation is the issuer's check, so a callee never reasons about a
chain it cannot see.

**The callee verifies offline**, in a fixed order, against the issuer's published key set
(JWKS): signature first — nothing in an unsigned token is believed — then lifetime with a
small clock leeway, audience is itself, chain depth, the called capability is in `scope`, its
declared effect is under the ceiling. Keys come only from the published set, never from the
token's header (`jku`, `jwk`, `x5u`). Then it acts for `sub`, names the outermost actor as its
caller and records the chain with the work. The issuer must be up to mint; with no issuer a
call fails closed — never back to a borrowed credential.

**The issuer is not the route.** Calls carrying a token go **direct**, caller to callee, as
`Authorization: Bearer`. Where something in the middle forwards a call because it holds the
product's credential, the delegation token rides in a header of its own beside it, so the
callee sees the chain whichever way the call came. Where this meets
the gateway (this file's own rule, not Fabric's): a gateway still enforces per-tool policy,
but the identity worth recording on its audit trail is the token's chain, not "the gateway
called".

**The host credential is the host's.** A service's own descriptor token is for its host —
discovery, events, usage, login — and, once callers can mint, is not presented to call a
capability; existing callers that borrow it switch when the issuer exists. A
token never travels in a URL, an argument vector, a tool's arguments, a log line or a usage
report.

**Money is a separate check against a meter.** The token's remaining-spend figure informs and
never authorizes. Before spending, the callee asks the meter with a token **of its own**:
exchanged onward with `aud` = the meter and read-only scope, because the token it holds names
itself as audience and cannot be handed over. The meter reserves against the grant's windows
and every level above (Fabric: the estate total), and refuses `limit-reached` **naming the
window** that ran out — a limit refusal without its window cannot be acted on.

**An approval is a document, not a ceremony.** When an action needs a person, the callee
refuses `approval-required` with the action's digest — SHA-256 of its RFC 8785 canonical
JSON, so two encodings of one action cannot get two digests. The action must be plain JSON
values: a date, a map or an `undefined` member would serialise as `{}` and let two actions
share a digest, so the canonicaliser refuses them.
The approval is a signed document over that digest, the one callee, the approver and the
method, consumed once by `jti` in a store that survives a restart. Order: token, then the
meter, then consume the approval, then act — an approval is not spent when the meter refuses.

**One refusal vocabulary** for authorisation only — `unauthenticated`, `token-expired`,
`wrong-audience`, `scope-not-granted`, `effect-above-ceiling`, `no-grant`, `grant-revoked`,
`limit-reached`, `approval-required`, `chain-too-deep`, `issuer-unavailable`, … (Fabric's
full set is seventeen). Transport and product errors keep their own codes; an unknown state is
a denial.

**What it does not buy.** A token file readable by the operator's account is readable by any
process of that account. Delegation gives every hop an attributable name, narrowing and
per-caller limits; it does not protect against a hostile local process. That takes an
approval or a device check — and proof of possession (DPoP, mutual TLS) is a further step this
shape leaves open.

**Worked example.** Fabric's `fabric-delegation/0.1` (contract DEC-0039, decided in Fabric
ADR-0144) implements the token, the verifier, the meter flow, the approval and the refusal
codes above — with schemas, positive/negative/semantic fixtures and a reference verifier: `docs/specification/delegation.md` in `passioncode-ai/fabric-agent-contract`
at `8e49fbd`. Read its check table (DL-13) before writing a verifier in another language.
The trust tiers are Fabric ADR-0144 amendment 4 (`19ad05ca`), in Fabric's main since
`5bf15e5c`, and the operator's decision is recorded in `passioncode-ai/fabric-workspace`
`knowledge/authority.md`, *Trust by machine*, at `714808ac`.

## agentgateway, concretely

A unified HTTP and gRPC proxy written in Rust — a control plane and a data plane — under the
Linux Foundation, Apache-2.0. It covers three planes at once:

| Plane | What it does |
|---|---|
| **LLM providers** | OpenAI-compatible routing across 20+ providers (OpenAI, Anthropic, Bedrock, Azure, Gemini, Cohere, Ollama, …) |
| **MCP** | tool federation across many servers, per-client authorization |
| **A2A** | inter-agent calls, capability discovery |

**Local configuration — and read this before copying an example.** The current top-level keys
are `config`, `gateways`, `routes` / `tcpRoutes`, `llm`, `mcp`, `ui`, plus `services` /
`workloads` for advanced backends. **`binds` is the deprecated predecessor to `gateways`** —
and the project's own overview page still introduces it, which is exactly the kind of drift
this skill's rule zero exists for. A minimal MCP config:

```yaml
mcp:
  port: 3000
  targets:
    - name: everything
      stdio:
        cmd: npx
```

**Security policies** available as first-class config: JWT authentication, API-key
authentication, HTTP authorization, external authorization, and **MCP-specific
authorization** — the last being the per-tool control that a generic gateway lacks.

**On Kubernetes** it is conformant to the **Gateway API** — `HTTPRoute`, `GRPCRoute`,
`TCPRoute`, `TLSRoute` — so it uses standard resources rather than a proprietary CRD set.
That is the strongest single argument for it in a cluster that already runs Gateway API: the
routing objects are ones your platform team already reviews.

## The gateway is where the lethal trifecta gets assembled

A gateway's whole value is composing many servers into one surface, and that is exactly the
operation that can create a risk none of its inputs had. The **lethal trifecta** — private
data, untrusted content, and the ability to communicate externally — is a property of the
**tool set in a session**, so every upstream can pass its own review and the composition
still be unsafe.

Two consequences for whoever runs the gateway:

- **A role is a trifecta decision, not only a least-privilege one.** Granting a role one
  more server is the moment to ask which of the three corners it just completed — not
  whether that server is individually trustworthy.
- **Per-tool annotations do not answer it.** They are hints about one tool (`readOnlyHint`,
  `destructiveHint`, `idempotentHint`, `openWorldHint`, and their defaults assume the
  dangerous shape — `agent-harness/references/tools.md`), and no combination of per-tool
  hints computes a session-level property.


## Traps

- **Introducing a gateway and leaving the direct paths open.** The policy is then advisory.
- **`prefixMode: conditional` plus a second target**, silently renaming every tool.
- **Copying a config from a blog post.** `binds` versus `gateways` is a live example; the
  config surface moves faster than the articles.
- **Treating the gateway as the security boundary.** It is *a* boundary. The sandbox, the
  credentials and the per-hop policy are the others.
- **Federating servers you do not trust into one namespace.** Federation makes a hostile
  server's tools look exactly as legitimate as everyone else's.
- **Calling a service with its own descriptor token.** It works, it is unattributable, and it
  hands the caller everything that token can do. Mint a delegation token for that one call.
- **`aud` as an array, or a token without `typ`.** Both let one signed document be replayed
  where it was never meant to be accepted.
- **Checking spend from the token's claim.** It was the remainder at mint time; the meter
  decides.
- **Forgetting the reconnect.** MCP notification delivery is best-effort; a hop in the middle
  makes a dropped subscription more likely, not less. Poll as well.
