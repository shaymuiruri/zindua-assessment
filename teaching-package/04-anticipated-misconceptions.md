# Anticipated Misconceptions

The three most common conceptual errors learners make when first encountering authentication and authorization in Django REST Framework.

---

## Misconception 1: "The token contains the password, so it's what proves who you are."

**The misconception stated clearly:**  
A learner sees that they send their email and password to `/auth/login/` and receive a token back. They conclude that the token is a transformed or encrypted form of their password, and that the server decrypts the token to find their credentials on each subsequent request.

**Why a learner naturally arrives here:**  
The login flow looks like a transaction: you give something (credentials) and receive something (token) in return. The natural inference is that what you receive contains what you gave. This mirrors everyday experience — a cloakroom ticket "contains" the number of your coat. It is also consistent with how some older authentication systems actually worked (Basic Auth sends the password on every request encoded as Base64, which looks superficially similar to a JWT).

**How to correct it without making the learner feel foolish:**  
Start by validating the intuition. "That guess makes sense because the login request and the token arrive back-to-back. But in this app, the token is not a hidden password — it is a signed receipt that says the user logged in successfully."

Then demonstrate: paste the token into jwt.io and decode it live. Show that the payload contains `user_id`, `exp`, and `token_type` — but no password, no email, nothing sensitive. In this project, the password is checked once in `POST /api/v1/auth/login/`; after that, the token is what the client presents on every request. The server checks the signature and then uses the `user_id` claim to find the user in the database.

The password is never in the token. The token does not prove you know the password — it proves that *someone who knew the password logged in at some point and was issued this token*. That is a subtle but important distinction.

---

## Misconception 2: "If I check the role in the token, I don't need to check the database."

**The misconception stated clearly:**  
After adding a `role` claim to the JWT payload, a learner writes their permission class to read `role` from the decoded token rather than from `request.user.role` (which pulls from the database). Their reasoning: "The role is already in the token — why make a database call?"

**Why a learner naturally arrives here:**  
The whole point of JWTs, as they have just learned, is to avoid database lookups on every request. The token is self-contained. If the user's role is in the token and the token is cryptographically verified, it seems logical that reading from the token is both faster and sufficient. This is not an irrational conclusion — it follows directly from the statelessness lesson.

**How to correct it without making the learner feel foolish:**  
Acknowledge that they have correctly understood why JWTs exist. "You're right that JWTs are designed to reduce database calls. For a menu or dashboard label, reading role from the token can be fine. But for access control in this app, the database still has to be the source of truth."

Walk through this scenario: imagine a learner account is changed from `STUDENT` to `OBSERVER` in the database after an admin review. If the permission class trusts the role claim already sitting inside an old token, the change will not take effect until the token expires. If the permission class reads from the database, the new role applies immediately on the next request.

The token payload is appropriate for the *client* to read (to personalize a UI, decide which buttons to show, etc.). The server's permission classes should always read from the database, where the source of truth lives. This is why, in `core/settings.py`, the teaching comment notes that the role in the token is "display-only on the client side."

---

## Misconception 3: "Once I check the role, the endpoint is secure."

**The misconception stated clearly:**  
A learner successfully adds `IsObserver` permission to the feedback endpoint and believes the endpoint is now secure. They have verified that non-observers get a 403. It does not occur to them that two different observers logged in at the same time could see each other's linked students' data.

**Why a learner naturally arrives here:**  
Role-based access control is taught as the solution to authorization. The learner has just learned to categorize users into roles and gate endpoints by role. They apply the lesson: "Observers can see feedback; non-observers cannot." This is correct as far as it goes. The error is that the lesson stopped one level above where it needed to go. Nothing in the typical RBAC explanation hints that users within the same role might need to be restricted from each other's data.

**How to correct it without making the learner feel foolish:**  
Use the hands-on task. Before explaining the bug, let the learner create a second observer account and try to access the first student's feedback. When they get a 403 because no `ObserverLink` row exists, ask them to explain the difference between "same role" and "same relationship." If they can say, "the new observer is valid, but not linked to this student," they have understood the point.

The correction is to draw the distinction between role-level and row-level explicitly. "Role-level says: *these kinds of users can reach this endpoint*. Row-level says: *this specific user can see this specific piece of data*. In most real applications, you need both. The role check gets you through the door; the row-level check decides which room you can enter."

Then name the consequence of missing the row-level check in plain terms: "If we only checked the role, any observer could read any student's data by changing the submission ID in the URL. In this assessment app, that means one observer could inspect a student they were never assigned to." Naming the exact failure makes the correction stick.