# Slack

The rep interface. A Bolt app (Python, `slack_bolt`) with App Home, DMs, interactive cards, a modal for Edit, and one slash command. See `slack/SPEC.md`, `slack/cards.md`, `slack/manifest.yml`.

## Why code here

Slack's interaction endpoint must acknowledge within 3 seconds; the Edit action opens a modal (`views.open`); App Home is rebuilt per user on `app_home_opened`. Flow tools handle this badly and Zapier cannot host the endpoint. The app is small.

## Scopes (from the manifest)

`app_mentions:read, chat:write, chat:write.public, commands, im:history, im:write, users:read, users:read.email`. `users:read.email` maps Slack users to Salesforce users by email; nothing else reads email.

## Events

`app_home_opened` (rebuild the board), `message.im` (reps can type "snooze Larkspur 3d" or "why is Larkspur P1"; a small parser handles three verbs and otherwise points at the card).

## Hosting

The Bolt app runs as one small service (a container in Meridian Travel's cloud, or Slack's Socket Mode from a worker if a public endpoint is not wanted). Socket Mode avoids exposing a URL but still needs a running process; the manifest is written for HTTP and flips to Socket Mode with two lines.

## Rate limits

Posting 500 P1 DMs at 07:00 local per timezone bucket stays under `chat.postMessage` limits (1 per second per channel is the tight one; DMs are separate channels). App Home publishes are per user on open, not pushed.

## To verify

- [ ] Meridian Travel is on Slack (not Teams) and an internal app can be installed by the workspace admin.
- [ ] Whether SteadyBase's trigger Slack delivery and Centralize's Slack app should post into the same pod channels, or Navigator should be the only voice.
