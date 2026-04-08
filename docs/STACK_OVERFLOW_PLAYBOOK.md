# Stack Overflow playbook (Random Tactical Timer)

Stack Overflow is for **specific technical questions with verifiable answers**. It is **not** a distribution channel for bulk or automated posts. Used well, it builds reputation and surfaces the app **only when it genuinely helps**.

## Rules that keep you out of trouble

1. **Answer the question first.** Solve the problem with code, explanation, or a correct pattern. A link-only or “use my app” answer is spam and will be deleted or downvoted.
2. **Disclose affiliation** when you mention your product (see template below). Stack Exchange’s [policy on promotion](https://stackoverflow.com/help/promotion) applies.
3. **No unsupervised posting.** Do not wire CI, agents, or scripts to **submit** answers, comments, or votes automatically. **Humans** must post the final text. (Read-only tooling is fine—see below.)
4. **Relevance bar.** Mention Random Tactical Timer only when the thread is clearly about something the app demonstrates (e.g. SwiftUI timer patterns, StoreKit quirks, foreground service audio on Android)—and even then, prefer a **minimal** store link in a footnote after a full technical answer.
5. **One account, real identity.** Sockpuppets and coordinated voting violate site rules.
6. **Answer drafts live in the repo.** Any Stack Overflow answer produced with tooling (or for CEO copy/paste) must be saved as a Markdown file under `marketing/referral_content/stackoverflow_answers/` using `{question-id}-{short-slug}.md` (see that folder’s `README.md`). Chat-only dumps are not the handoff format.
7. **Cite our code.** Each draft must link to **real** usage in this repository on `develop` (`https://github.com/IgorGanapolsky/Random-Timer/blob/develop/...`) for every pattern we claim we use. If we do not implement something (e.g. a hypothetical API), state that and keep that portion generic—no fake file links. Include **affiliation disclosure** when linking our repo (see snippet below).

## Disclosure snippet (paste under your answer when you mention the app)

```text
Disclosure: I work on Random Tactical Timer (iOS/Android). The link is only for context; the answer above stands on its own.
```

## Tags worth watching (mobile + overlap with this codebase)

Use **Newest** or **No answers** filters. A generated list with direct links lives in:

`marketing/referral_content/stackoverflow_watchlist.md` (refreshed by the weekly referral script).

High-signal areas for this project:

| Area | Example tags |
|------|----------------|
| iOS UI | `swift`, `swiftui`, `ios` |
| Apple billing | `storekit`, `in-app-purchase` |
| Android UI | `android`, `android-jetpack-compose`, `kotlin` |
| Android billing | `google-play`, `billing`, `android-billing` |
| Background work | `foreground-service`, `avfoundation` (when relevant) |

## What “good” looks like

- You fix a `Timer` / `Task.sleep` / lifecycle bug in SwiftUI and, in passing, note that you hit the same issue shipping a timer app—with disclosure and one link.
- You explain Play Billing or StoreKit 2 flow with code from **documentation**, and add “we ship this pattern in production” + link.

## What to avoid

- Posting the same canned paragraph on many threads.
- Answering duplicates without closing as duplicate.
- “Check out my app” without solving the OP’s problem.

## Metrics

Track qualitatively: accepted answers, upvotes, and **lack of** spam flags—not raw link count.

## Automation you *can* use (real-time discovery — not posting)

These reduce lag **finding** questions; they do **not** replace writing a correct answer.

| Approach | Role | Post to SO? |
|----------|------|-------------|
| **RSS / Atom** | Official tag feeds; refresh in a reader or script | No |
| **`scripts/stackoverflow_feed_triage.py`** | CLI: prints newest questions for given tags (markdown or JSON) | No |
| **Stack Exchange API** | Read questions; optional app key for higher quotas; still **no** write without human gate | Only if *you* call write endpoints after review |
| **MCP / IDE agents** | Fetch feed or page, **draft** into `marketing/referral_content/stackoverflow_answers/*.md` | You paste from the file; bot does not submit |
| **Browser automation** | Same as MCP: open thread, assist drafting—**do not** auto-submit bulk answers | High risk if unattended |

**Why not “answer in real time” with full automation?** LLM answers without expert review are often wrong; bulk posting triggers spam detection and damages your account and the site. Use automation to **notify and draft**; **you** verify, fix, and click Post.

### Example (local triage)

```bash
uv run python scripts/stackoverflow_feed_triage.py --tags swiftui,storekit --limit 10
```

## Deal: your hourly “RSS” + copy/paste digest

**You** write and paste answers on Stack Overflow (policy-safe). The repo gives you **two** read-only streams:

### A) Real Atom feeds (subscribe in any RSS reader)

Stack Overflow hosts the feeds; they update when **new questions** appear (often within minutes).

- **In repo:** `marketing/referral_content/stackoverflow_subscribe_atom_feeds.md` — copy each **Feed URL** into Feedly, Inoreader, Outlook, etc.
- **Regenerate locally** after editing tag groups:

```bash
uv run python scripts/stackoverflow_feed_triage.py \
  --write-subscribe-markdown marketing/referral_content/stackoverflow_subscribe_atom_feeds.md \
  --tag-groups-file marketing/data/stackoverflow_digest_tag_groups.txt
```

Tag groups live in **`marketing/data/stackoverflow_digest_tag_groups.txt`** (one line per feed).

### B) Hourly snapshot ZIP (question links in one file)

Workflow **`stackoverflow-hourly-digest.yml`** runs **every hour** (~:12 UTC) on the default branch once merged.

**Actions** → **Stack Overflow hourly triage digest** → open a run → download artifact **`stackoverflow-hourly-digest`**. It contains:

- **`digest.md`** — latest questions per tag group (for copy/paste into the browser).
- **`SUBSCRIBE_ATOM_FEEDS.md`** — same feed URLs as (A).

Nothing is posted to Stack Overflow from CI.
