# Learning Objectives

By the end of this 60-minute session, learners will be able to:

---

## Objective 1
**Distinguish authentication from authorization and name the Django component responsible for each.**

*Specific observable form:* When given a 401 response and a 403 response, the learner can explain in writing what caused each one, which layer of the system produced it, and what would need to change to fix it.

*How I assess it:* At the end of the session I show two error responses on screen. Learners write a one-sentence explanation for each on a sticky note (or in a shared doc). I read them and respond to any that conflate the two.

---

## Objective 2
**Decode a JWT access token and identify at least three claims it contains, including the user's ID.**

*Specific observable form:* Given an access token returned by `POST /api/v1/auth/login/`, the learner can paste it into jwt.io, point to the `user_id`, `exp`, and `token_type` fields in the payload, and explain what each one means.

*How I assess it:* During the demo I hand a token to a learner and ask them to paste it into jwt.io while sharing their screen. The rest of the group confirms whether the fields are identified correctly.

---

## Objective 3
**Add a role claim to the JWT issued by `POST /api/v1/auth/login/` and verify that it matches the logged-in account.**

*Specific observable form:* The learner can update a `TokenObtainPairSerializer` subclass so the login response includes a `role` claim, then decode the token and point to the exact value for instructor, student, and observer accounts.

*How I assess it:* This is checked in the follow-up exercise after the session, not inside the 60-minute slot. Learners submit the serializer change plus a decoded token screenshot that shows the role claim changing when the account changes. *(Inside the session, objective 2 is the bridge: if they can decode claims, they are ready to add one.)*

---

## Objective 4
**Write a custom DRF permission class that blocks or allows a request based on the user role.**

*Specific observable form:* The learner can write a class that subclasses `BasePermission`, implements `has_permission`, checks `request.user.role`, and returns the correct boolean for the request. They can also explain why `is_authenticated` must be part of the check, not just the role string.

*How I assess it:* In the live code read, I ask learners to explain the `IsObserver` class in `classroom/permissions.py`. If they can predict why an unauthorised observer gets a 403 before we run the request, they have met the objective. The follow-up exercise asks them to create a new permission class for a made-up `TA` role that can read submissions but cannot leave feedback.

---

## Objective 5
**Explain why the Observer needs a row-level check and trace the `ObserverLink` lookup that enforces it.**

*Specific observable form:* The learner can explain, without opening the file, why `request.user.role == 'OBSERVER'` is not enough for `GET /api/v1/submissions/{id}/feedback/`, and can name both the `ObserverLink` model and the `.exists()` lookup used to decide access.

*How I assess it:* At the end of the session, I ask one learner to narrate the observer 403 back to the class. I follow up with: "If we removed the `ObserverLink` filter, what exact mistake would the API make?" A correct answer must mention that any observer could see any linked student's data.