# Collaborative Development Task

- source_template_gid: `1213441914697823`
- export_strategy: `instantiate_project_template`
- format_version: `1`
- import_mode: `create_new_versioned_template`
- next_version_name: `Collaborative Development Task vNEXT`
- instantiated_project_gid: `1213754294945032`
- requested_dates: `Start Date=2026-03-19`

## Untitled section

_No tasks_

## Initiating

- Confirm ticket exists, is assigned, authorized, and aligned with broader goals
  source_gid: `1213754562651541`
- Verify budget approval
  source_gid: `1213754295061554`
- Identify Stakeholders - who needs to be consulted or informed?
  source_gid: `1213754295061560`

## Planning

- Surface scope or timeline uncertainty to the right person before work begins
  source_gid: `1213752357302923`
- Document Existing Solution, Scope, Acceptance criteria, Technical, Estimate, Deadline, QC, and Deployment
  source_gid: `1213752357276236`
  depends_on_source_gids: `1213754562651541`
- Risk identification — what could go wrong or cause a delay?
  source_gid: `1213752357272894`
- If bug, verify repeatable
  source_gid: `1213752357302918`
  depends_on_source_gids: `1213754562651541`

## Monitoring & Controlling

- Document decisions and scope changes in Jira as they happen
  source_gid: `1213754562651547`
  depends_on_source_gids: `1213754562651541`
- Check regularly: still on scope, on track, and no active risks? If not, escalate before it compounds.
  source_gid: `1213752357272899`

## Executing

- Jira ticket status updated to In Progress
  source_gid: `1213754562651533`
  depends_on_source_gids: `1213752357276236`, `1213754295061554`, `1213754562651541`
- Can you create a small automated test that fails?
  source_gid: `1213752357302928`
  depends_on_source_gids: `1213754562651533`
- Implement the solution
  source_gid: `1213752357302933`
  depends_on_source_gids: `1213752357276236`, `1213752357302918`, `1213754562651541`
- Verified: anonymous, empty state, and no regression against existing implementation.
  source_gid: `1213752357302938`
  depends_on_source_gids: `1213752357302933`, `1213754562651533`
- Code formatting and comments follow standards
  source_gid: `1213754562651553`
  depends_on_source_gids: `1213752357302938`
- Confirm automated test (if it exists) now passes
  source_gid: `1213754562651559`
  depends_on_source_gids: `1213752357302928`, `1213754562651533`
- Diffy run completed and passing.
  source_gid: `1213754295061548`
  depends_on_source_gids: `1213752357302933`
- Branch and PR follow naming conventions (JIRA-TICKET-NUM format)
  source_gid: `1213752357302943`
  depends_on_source_gids: `1213754562651533`
- Testing instructions, screenshots, and multidev links prepared for QC request
  source_gid: `1213752650471407`
- Reviewers assigned in GitHub and notified via Slack with PR link
  source_gid: `1213752650471389`
  depends_on_source_gids: `1213752650471407`
- Jira ticket status moved to Code Review
  source_gid: `1213752650471394`
  depends_on_source_gids: `1213752357302933`, `1213752650471389`, `1213752650471407`
- PR approved — all review comments resolved.
  source_gid: `1213752650471401`
  depends_on_source_gids: `1213752357302933`, `1213752650471389`
- Jira ticket status updated to QC/Test
  source_gid: `1213752650471413`
  depends_on_source_gids: `1213752650471394`, `1213752650471401`
- QC Passes
  source_gid: `1213752357305121`
  depends_on_source_gids: `1213752650471413`

## Closing

- Brief retrospective note logged in Jira — anything worth carrying forward to the next task?
  source_gid: `1213752357272904`
- Deployment task created and linked
  source_gid: `1213752357305106`
- (optional) PR branch deleted / Or (approved) added to PR
  source_gid: `1213752357305111`
- Follow up tasks created, if needed
  source_gid: `1213752357305116`
