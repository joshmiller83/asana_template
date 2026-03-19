# Deployment Task

- source_template_gid: `1213546897782557`
- export_strategy: `instantiate_project_template`
- format_version: `1`
- import_mode: `create_new_versioned_template`
- next_version_name: `Deployment Task vNEXT`
- instantiated_project_gid: `1213752357343617`

## Untitled section

_No tasks_

## Discovery

- Deployment ticket created in Jira (format: SiteName: Deployment) in RT1 stream, with date/time ET and list of PRs included
  source_gid: `1213752650515580`
- Budget and stakeholder approval confirmed
  source_gid: `1213752357350722`
- All PRs to be deployed are approved and are not merged to main
  source_gid: `1213752650515585`
- Confirm the day after deployment is not a public holiday
  source_gid: `1213752650515590`
- Latest config exported from Live, compared, committed, and merged to main via PR
  source_gid: `1213752357350727`

## Plan Alignment

- Deployment date/time confirmed with stakeholder and product manager (avoid high-traffic events, conferences, VIP access windows)
  source_gid: `1213752650515595`
- Pre-deployment notification sent 2–3 days ahead and day-of to: Josh Miller, David Connell, Sam Cressman, Jerry Ta, David Hislop, WebDev Team
  source_gid: `1213752650515600`
- If high-profile/high-traffic site: Graham MacDonald, Jess Kelly, and Bob Broughman also notified
  source_gid: `1213752357350732`
- If high-profile/high-traffic site: Pantheon support ticket opened requesting extra vigilance
  source_gid: `1213752357350737`
- Confirmed backup person available for after hours deployment
  source_gid: `1213752650480353`

## The Deployment

- Latest Live database cloned to Test environment
  source_gid: `1213752357350742`
- Features QC'd thoroughly on Dev/Test environment
  source_gid: `1213752357350747`
- Diffy VRT run between Test and Live — screenshots reviewed and marked complete
  source_gid: `1213754295091945`
- Live site backup created on Pantheon (database minimum, full backup preferred)
  source_gid: `1213754295091951`
- New Relic open and monitoring
  source_gid: `1213754295091957`
- Site put in maintenance mode — wait for Web Transactions Time graph to settle
  source_gid: `1213754295091963`
- Deploy log on Pantheon updated with PRs included
  source_gid: `1213754295091969`
- Code deployed from Test to Live
  source_gid: `1213754295091975`
- Configs imported (automatic or manual depending on site) and cache cleared
  source_gid: `1213753868341677`
- Status Report and Recent Log Messages reviewed
  source_gid: `1213753868341683`
- Admin and content menus spot-checked
  source_gid: `1213753868341689`
- Any deployment-specific tasks completed (node creation, content configuration, etc.)
  source_gid: `1213753868341695`
- Site taken off maintenance mode
  source_gid: `1213753868341701`

## Follow-Through

- Team notified via Slack/email that deployment is complete, including features deployed and minutes in maintenance mode
  source_gid: `1213752650421176`
- Jira ticket status updated to Done
  source_gid: `1213752650421181`
- Pantheon ticket raised if anything seems off
  source_gid: `1213752650480358`
- Any post-deployment issues should be logged immediately
  source_gid: `1213752650421186`
