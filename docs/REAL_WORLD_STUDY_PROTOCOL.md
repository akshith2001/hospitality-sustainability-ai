# Proposed Real-World Study Protocol

## Status

This document is a research-design proposal, not confirmation that a study has ethical
approval or that real hospitality data have been collected. The final protocol must be
reviewed by the host university's ethics and data-protection processes before recruitment
or installation of monitoring equipment.

## Aim

Evaluate whether an explainable model can predict hospitality electricity consumption,
identify readings that justify investigation, and support practical sustainability
decisions without presenting predictions as proof of waste.

## Study duration and sampling

- Collect data for at least one full year to represent seasonal conditions.
- Record electricity automatically at 30-minute intervals using a calibrated smart meter.
- Retain a verified daily total for reconciliation and reporting.
- Collect daily operational context: customer count, opening hours, outside temperature,
  special events and documented equipment changes.
- Record meter calibration, outages and replacements so missing or unreliable periods can
  be identified rather than silently treated as normal data.

## Pseudonymisation and data minimisation

- Replace business names with random research identifiers such as `VENUE-0042`.
- Keep the re-identification key encrypted, separate from model-training data and accessible
  only to authorised research personnel.
- Do not place full venue addresses in training files. Use only a justified broad region,
  climate zone or non-identifying weather-station identifier where required.
- Do not collect employee names, employee numbers, email addresses, IP addresses or device
  identifiers with anonymous operational feedback.

## Permissions and voluntary participation

Venue permission and staff participation are separate:

1. An authorised venue representative provides organisational permission for meter
   installation and use of the venue's operational data.
2. Each staff participant independently decides whether to provide research feedback.

Staff participation must be voluntary. Refusal or withdrawal must not affect employment,
pay, shifts, references or workplace treatment. Managers should not receive a list of who
participated.

Before consent, participants receive a plain-language information sheet describing the
study purpose, collected data, access controls, retention schedule, security, withdrawal
process, anonymisation and planned outputs.

## Retention

Data and audit records must follow a documented retention schedule approved during ethics
and data-protection review. Personal or pseudonymous information must not be kept forever
or "just in case". At the end of the justified period, it should be securely deleted or
irreversibly anonymised. The schedule and any lawful research safeguards must be explained
before participation.

## Model evaluation

- Establish and publish a simple baseline alongside every model result.
- Reserve the newest month as an untouched chronological test period.
- Perform leave-one-venue-out evaluation for every participating venue.
- Report all venue results, including poor performance, plus the mean and worst result.
- Investigate weak venue performance for missing variables, meter issues or operational
  differences; do not hide it.
- Treat early models trained on only several weeks as preliminary.

## Alerts and feedback

An alert means that usage is unusual under the model; it is not proof of waste. Staff may
anonymously classify an alert as confirmed waste, equipment fault, special event,
incorrect data, normal operation or unknown.

Feedback begins as pending and cannot influence training unless an operations manager, a
sustainability reviewer and a research reviewer all approve it. Disagreement or a missing
decision keeps the record out of training.

## Deployment governance

- Retrain only after a verified repeated pattern, not one unusual reading.
- Compare a candidate with the current model on untouched data.
- Reject a candidate that worsens overall error or worst-venue performance.
- Require authorised human approval before deployment.
- Version models and retain the prior approved version for possible rollback.
- If monitored error exceeds the approved tolerance, pause AI recommendations and request
  human review rather than automatically replacing or rolling back the model.

Meter status and AI status remain separate. Verified raw readings may be displayed while
AI recommendations are paused. Unverified or faulty meter data are unavailable in normal
decision views, although authorised technical reviewers may access them for diagnosis.

## Auditability

Important state changes should be recorded in an append-only audit trail containing the
timestamp, component, previous state, new state, authorised reviewer role, reason and model
version. Ordinary venue staff cannot edit or delete records. Corrections are appended as
new entries. Audit retention follows the approved retention schedule.

## Required approvals before a pilot

- University research ethics approval
- Data-protection review and documented lawful basis
- Venue agreement and meter-installation permission
- Staff participant information and consent materials where staff data are involved
- Security, incident-response and access-control plan
- Predefined analysis, exclusion and model-promotion criteria

## Regulatory guidance

- [UK ICO: storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/)
- [European Commission: GDPR processing principles](https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/principles-gdpr/overview-principles/what-data-can-we-process-and-under-which-conditions_en)

These links are starting points, not legal advice. Requirements must be confirmed for the
countries and institutions involved in the final study.
