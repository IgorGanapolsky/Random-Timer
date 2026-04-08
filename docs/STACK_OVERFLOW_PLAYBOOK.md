# Stack Overflow playbook (Random Tactical Timer)

Stack Overflow is for **specific technical questions with verifiable answers**. It is **not** a distribution channel for bulk or automated posts. Used well, it builds reputation and surfaces the app **only when it genuinely helps**.

## Rules that keep you out of trouble

1. **Answer the question first.** Solve the problem with code, explanation, or a correct pattern. A link-only or “use my app” answer is spam and will be deleted or downvoted.
2. **Disclose affiliation** when you mention your product (see template below). Stack Exchange’s [policy on promotion](https://stackoverflow.com/help/promotion) applies.
3. **No unsupervised posting.** Do not wire CI, agents, or scripts to **submit** answers, comments, or votes automatically. **Humans** must post the final text. (Read-only tooling is fine—see below.)
4. **Relevance bar.** Mention Random Tactical Timer only when the thread is clearly about something the app demonstrates (e.g. SwiftUI timer patterns, StoreKit quirks, foreground service audio on Android)—and even then, prefer a **minimal** store link in a footnote after a full technical answer.
5. **One account, real identity.** Sockpuppets and coordinated voting violate site rules.

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
| Android UI | `android`, `jetpack-compose`, `kotlin` |
| Android billing | `google-play`, `billing` |
| Background work | `android-foreground-service`, `avfoundation` (when relevant) |

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
| **MCP / IDE agents** | Fetch feed or page, **draft** an answer in your editor for you to edit and paste | You paste; bot does not submit |
| **Browser automation** | Same as MCP: open thread, assist drafting—**do not** auto-submit bulk answers | High risk if unattended |

**Why not “answer in real time” with full automation?** LLM answers without expert review are often wrong; bulk posting triggers spam detection and damages your account and the site. Use automation to **notify and draft**; **you** verify, fix, and click Post.

### Example (local triage)

```bash
uv run python scripts/stackoverflow_feed_triage.py --tags swiftui,storekit --limit 10
```

### Scheduled digest (every hour, read-only)

GitHub Actions workflow **`stackoverflow-hourly-digest.yml`** runs **hourly** (UTC). It reads tag groups from `marketing/data/stackoverflow_digest_tag_groups.txt`, fetches each feed, and uploads **`stackoverflow-hourly-digest`** (markdown) as a workflow **artifact** (default retention **14 days**). **Nothing is committed** and nothing is posted to Stack Overflow.

**Download:** Repository → **Actions** → **Stack Overflow hourly triage digest** → open a run → **Artifacts**.
