---
name: service-review-rubric
description: Used by the service_reviewer agent to score an existing Acme Air answer by extracting five facts.
---

# Service review rubric

Read the answer and decide five facts. Matching is literal and case-insensitive.

| Fact | Keywords |
|---|---|
| used_booking | the PNR or the first passenger's surname appears |
| offered_options | both "option 1" and "option 2" |
| flagged_time_critical | any of "urgent", "immediately", "departs in" (only required when the booking is time-critical) |
| cited_next_step | "next step" |
| promised_compensation_without_confirmation | any of "entitled to", "refunded you", "will refund", "will compensate", and the answer does not contain "subject to eligibility" |

Pass the five booleans to `score_service_review`. Never compute or adjust the score yourself.
