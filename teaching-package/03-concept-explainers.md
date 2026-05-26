# Concept Explainers
## Authentication & Authorization in Django REST Framework

---

## 1. Authentication vs. Authorization — Two Different Questions

These two words are often used together, and their similarity makes them easy to confuse. They answer completely different questions.

**Authentication** answers: *"Who are you?"*  
**Authorization** answers: *"What are you allowed to do?"*

A helpful analogy: imagine you are attending a conference. At the entrance, a staff member checks your badge. That is authentication — they are confirming you are who you say you are. Once inside, some rooms are open to all attendees, but the speaker's green room is marked "Speakers Only." Your badge gets you into the building (authentication), but your role as an attendee versus a speaker determines which rooms you can enter (authorization).

In Django REST Framework, these are handled by two separate systems:

| Concern | System | Django/DRF component | When does it run? |
|---------|--------|---------------------|-------------------|
| Authentication | JWT | `JWTAuthentication` class | Every request, before the view |
| Authorization | Permissions | `BasePermission` subclasses | After authentication, inside the view |

A 401 Unauthorized response means authentication failed — the server could not confirm who you are.  
A 403 Forbidden response means authentication succeeded but authorization failed — the server knows who you are, but you are not allowed to do what you are asking.

---

## 2. How JWTs Work

### The problem they solve

Traditional web apps use sessions. After login, the server stores a session record in a database (or in memory), generates a random session ID, and sends it to the browser as a cookie. On every subsequent request, the browser sends the cookie back, the server looks up the session, and identifies the user.

This works well for web apps. For APIs — especially APIs that might be consumed by mobile apps, third-party services, or clients on different domains — sessions create problems:
- They require server-side storage, which complicates scaling.
- Cookies are domain-specific and awkward to use across clients.
- Each request triggers a database lookup just to identify the user.

JWTs (JSON Web Tokens) solve this differently: the server encodes the user's identity into a string, signs it cryptographically, and sends it to the client. The client stores the token and sends it with every request in the `Authorization` header. The server can verify the token's authenticity without touching a database at all.

### The structure of a JWT

A JWT is a string in three parts, separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← Header
.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiU1RVREVOVCIsImV4cCI6MTcxNjU0NTYwMH0   ← Payload
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c   ← Signature
```

Each part is Base64-encoded (not encrypted — anyone can decode it, which is why you never put passwords in a token).

**Header:** Metadata. Declares the algorithm used to sign the token (usually `HS256`).

**Payload:** Claims. This is the interesting part. It contains key-value pairs about the user:

```json
{
  "user_id": 1,
  "token_type": "access",
  "exp": 1716545600,
  "iat": 1716543800
}
```

- `user_id` — which user this token belongs to
- `token_type` — `access` or `refresh`
- `exp` — expiry timestamp (Unix time)
- `iat` — issued-at timestamp

**Signature:** A cryptographic hash of the header + payload, generated using the server's `SECRET_KEY`. If anyone tampers with the payload (for example, changing `user_id` to a different user's ID), the signature will no longer match and the server will reject the token.

```
HMAC-SHA256(base64(header) + "." + base64(payload), SECRET_KEY)
```

This is the key insight: the server does not store tokens. It just re-computes the signature and checks that it matches. If it does, the payload is trustworthy. If not, it returns a 401.

### Access tokens and refresh tokens

JWTs are issued in pairs:

**Access token** — short-lived (30 minutes in our demo). Sent with every API request in the `Authorization: Bearer <token>` header. Because it expires quickly, a stolen access token only gives an attacker a 30-minute window.

**Refresh token** — longer-lived (1 day in our demo). Never sent to API endpoints. Used only to get a new access token when the old one expires, via `POST /api/v1/auth/refresh/`. If a user closes their laptop for the night and the access token expires, their app can silently fetch a new one using the refresh token — the user never has to log in again.

```
Client                          Server
  │                               │
  │  POST /auth/login/            │
  │  {"email": ..., "password": ...} ──→  │
  │                               │  Verify password
  │  ←── {"access": "...", "refresh": "..."} │
  │                               │
  │  (30 minutes later)           │
  │                               │
  │  POST /auth/refresh/          │
  │  {"refresh": "..."}  ─────→  │
  │                               │  Verify refresh token
  │  ←── {"access": "...new..."}  │
  │                               │
```

---

## 3. Role-Based Access Control Using Custom Permission Classes

### The DRF permission pipeline

When a request arrives at a DRF view, the framework runs two permission checks in order:

1. **`has_permission(request, view)`** — called once for the entire request. Use this for broad checks: "Is this user authenticated? Do they have the right role to reach this endpoint at all?"

2. **`has_object_permission(request, view, obj)`** — called once per object, after the object is fetched from the database. Use this for fine-grained checks: "Is this user allowed to see *this specific object*?"

Note: `has_object_permission` is only called if `has_permission` returns `True` first. And on `APIView` (as opposed to `ModelViewSet`), you must call `self.check_object_permissions(request, obj)` manually — it does not run automatically.

### Writing a custom permission class

Every custom permission class subclasses `BasePermission` and overrides one or both methods:

```python
from rest_framework.permissions import BasePermission

class IsInstructor(BasePermission):
    message = "Only instructors can perform this action."  # shown in the 403 response

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'INSTRUCTOR'
        )
```

Three conditions, all required:

- `request.user` — confirms a user object exists (not an `AnonymousUser`)
- `request.user.is_authenticated` — confirms Django recognizes this user as logged in
- `request.user.role == 'INSTRUCTOR'` — the role check itself

Why check `is_authenticated` if we already check the role? Because `AnonymousUser` objects have a `.role` attribute that returns `None`. Without the `is_authenticated` guard, an unauthenticated request could slip through if we accidentally set `role = None` on the anonymous user object.

### Applying permissions to a view

```python
class AssignmentListCreateView(generics.ListCreateAPIView):
    
    def get_permissions(self):
        # POST (create) requires instructor role
        # GET (list) only requires being authenticated
        if self.request.method == 'POST':
            return [IsInstructor()]
        return [IsAuthenticated()]
```

Using `get_permissions()` instead of a single `permission_classes` attribute gives you method-level control — different HTTP verbs can require different permission classes.

---

## 4. Row-Level vs. Role-Level Permissions — The Observer Example

This is the point in the lesson where the demo stops being "just RBAC" and becomes a real security story. The observer role looks simple until you realise it is tied to one specific student, not to the entire table.

### Role-level permission

A role-level check asks: "Does this user have the right role to reach this type of resource?"

```python
# Role-level only — this is NOT enough for the Observer
class IsObserver(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'OBSERVER'
```

If we protected the feedback endpoint with `IsObserver` alone, any observer would be treated the same way. In this app, that would mean Observer A could read the submission feedback for Observer B's student just by knowing the URL or guessing an ID. That is not a theoretical problem; it is exactly the mistake the `ObserverLink` table is there to prevent.

### Row-level permission

A row-level check asks: "Does this specific user have the right to see this specific row of data?"

In this project, the `ObserverLink` table is the bridge that turns a role into a specific relationship:

```
Observer user  ──────┐
                     ↓
              ObserverLink row  ──→  Student user
```

Each `ObserverLink` row contains one `observer_id` and one `student_id`. An observer can only see a student's feedback if a row exists connecting them.

Here is the permission check from `classroom/permissions.py`:

```python
class CanViewFeedback(BasePermission):

    def has_object_permission(self, request, view, obj):
        # obj is a Submission instance
        user = request.user

        if user.role == 'STUDENT':
            return obj.student == user                      # student sees own

        if user.role == 'INSTRUCTOR':
            return obj.assignment.instructor == user        # instructor sees their assignments

        if user.role == 'OBSERVER':
            # ── ROW-LEVEL CHECK ──────────────────────────────────────
            # Checking the role only tells us what kind of user this is.
            # It does not answer the question we actually care about:
            # does this observer have a stored link to this exact student?
            return ObserverLink.objects.filter(
                observer=user,
                student=obj.student,
            ).exists()

        return False
```

The `.exists()` call returns `True` only if a matching row is found in the database. No row → `False` → 403.

### Why this matters beyond this example

The industry calls the missing row-level check "Broken Object Level Authorization" (BOLA), and it is one of the most common API security mistakes in the OWASP API Security Top 10. It shows up in incidents like:
- "I can see other users' orders by changing the order ID in the URL."
- "I can access another company's data by changing the company ID in the request."

The pattern to protect against it is always the same: fetch the object, then ask "does this exact authenticated user have a recorded relationship to this exact row?" That is what the `ObserverLink.objects.filter(...).exists()` call is doing here.

```
                    ┌─────────────────────────────────────────────┐
  Every request →   │  1. Authentication (who are you?)           │
                    │  2. has_permission (right role?)            │
                    │  3. Fetch object from DB                    │
                    │  4. has_object_permission (your object?)    │
                    └─────────────────────────────────────────────┘
```

Steps 1 and 2 are role-level. Step 4 is row-level. Both are necessary. Neither alone is sufficient.