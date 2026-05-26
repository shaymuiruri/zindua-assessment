# Session Outline — Authentication & Role-Based Access Control in Django REST Framework

**Session duration:** 60 minutes  
**Assumed prior knowledge:** Learners have built basic Django views and created their first DRF API. They have not implemented authentication or permissions before.

---

## The 60-Minute Plan

| Time | Activity | Format |
|------|----------|--------|
| 0:00 – 0:05 | **Hook: the unlocked API** | Discussion |
| 0:05 – 0:20 | **Concept block: Auth vs. authz, JWTs** | Explanation + diagram |
| 0:20 – 0:35 | **Demo walkthrough: login → token → request** | Live Postman demo |
| 0:35 – 0:50 | **Guided code read: permissions.py** | Code walkthrough |
| 0:50 – 0:58 | **Hands-on: break the observer** | Learner task |
| 0:58 – 1:00 | **Close: what comes next** | Summary |

---

## Segment-by-Segment Breakdown

### 0:00 – 0:05 — Hook: The Unlocked API

**What happens:** I open Postman and hit our `GET /api/v1/assignments/` endpoint with no authentication header. It returns a 401. Then I ask: "What if this endpoint had no protection? Who could read it?"

Learners call out answers. We land on the obvious problem: without authentication, any person with the URL can read your data.

**Why I start here:** Adult learners engage best when the problem precedes the solution. Five minutes spent making the vulnerability feel real is worth more than five minutes of theory. It also gives me a diagnostic — I can tell immediately how much the group already knows by what they say.

---

### 0:05 – 0:20 — Concept Block: Auth vs. Authz, JWTs

**What happens:** I walk through three concepts with the whiteboard diagram from the concept explainers:

1. **Authentication vs. authorization** — two separate questions, two separate systems.
2. **How JWTs work** — the three-part structure, what the payload contains, why they are used over session cookies for APIs.
3. **How the DRF permission pipeline works** — `has_permission` runs first (broad), `has_object_permission` runs second (specific).

I spend roughly 5 minutes on each concept. I keep it conceptual — no code yet.

**Why before the demo:** Learners who see the demo before understanding the concepts watch without being able to follow along. They see Postman responses but don't know what questions to ask. The concept block gives them the vocabulary to understand what they are about to see.

---

### 0:20 – 0:35 — Demo Walkthrough: Login → Token → Request

**What happens:** I open Postman and walk through the demo app live, narrating every step:

1. `POST /auth/login/` as the instructor. Show the access token and refresh token in the response. Point out the three-part JWT structure. Decode the payload live at [jwt.io](https://jwt.io) — "look, the user's role is right there."
2. `GET /api/v1/assignments/` with the instructor's token. Shows the instructor's assignments.
3. Same endpoint with the student's token. Shows only enrolled assignments. "Same endpoint, different data — that's role filtering."
4. `GET /api/v1/submissions/1/feedback/` as the observer. "This observer is linked to this student. They can see the feedback."
5. **Token refresh live:** Let the access token expire (or manually edit the expiry in the demo to 1 second), then call `POST /auth/refresh/`. New token arrives. "The user never had to log in again."

**Why this order:** Login → use token → demonstrate role difference → demonstrate row-level → demonstrate refresh. Each step builds on the last. Learners see the complete journey in one pass before we open the code.

---

### 0:35 – 0:50 — Guided Code Read: permissions.py

**What happens:** I share my screen in the editor (not slides) and walk through `classroom/permissions.py`. I read the teaching comment at the top aloud, then walk through:

- `IsInstructor` — "Three conditions on one line. What happens if we forget `is_authenticated`?"
- `CanViewFeedback.has_object_permission` — "Notice we check role first. But for the Observer, we go to the database. Why?"
- The `ObserverLink.objects.filter(...).exists()` call — "This is the row-level check. We are asking: does a link exist? Not just: is this person an observer?"

I pause after each section and ask a question. The questions are not rhetorical — I wait for answers.

**Why code over slides:** This is the session's pivot point. Learners are about to try a task. Showing them real, working code they can reference is more useful than a slide they cannot search or copy from.

---

### 0:50 – 0:58 — Hands-On: Break the Observer

**What happens:** I give learners one task:

> *"Create a second observer user (you can use the Django admin or the shell). Try to GET /api/v1/submissions/1/feedback/ using that new observer's token. What happens and why?"*

Expected result: 403 Forbidden. The new observer has no `ObserverLink` row connecting them to the student. The code path reaches `ObserverLink.objects.filter(...).exists()` and returns `False`.

Learners who finish early get a stretch task:
> *"Add a second student. Create a second ObserverLink connecting the new observer to the new student. Now try to access the first student's feedback. What do you expect? Test it."*

**Why this task:** It directly tests the row-level concept from the code read. The only way to get the right answer is to understand why the `ObserverLink` table exists. Correct failure (a 403) is the success condition — this is intentional. We are practising debugging by reading error responses.

---

### 0:58 – 1:00 — Close

I bring the group back together. I ask one learner to explain in their own words why the observer got a 403. I correct if needed, then close with:

- One-sentence summary of the auth/authz distinction.
- Three things to look up next: token blacklisting, rate limiting, OWASP Broken Object Level Authorization.
- Where to find this code for reference.

---

## Why This Order Overall

The session follows a **problem → concept → demonstration → code → practice** arc. Each stage answers a question the previous stage raised:

- *Hook* creates the question: "How do we protect an API?"
- *Concept block* answers it at the level of ideas.
- *Demo* makes the ideas concrete.
- *Code read* shows how the ideas become instructions.
- *Task* verifies that learners can reason from the code, not just follow it.

The one thing I deliberately avoid is giving learners code to copy. The task requires them to operate the running system and read error responses. Understanding comes from that friction, not from reproducing a working example.