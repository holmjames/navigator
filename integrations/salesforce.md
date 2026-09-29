# Salesforce

System of record. Navigator reads it nightly and writes tasks, events, opp stage changes, and a handful of custom fields through the API. It is never a second CRM.

## Read (nightly, native Snowflake connector or Fivetran)

| Object | Fields |
|---|---|
| Account | `Id, Name, Website, Industry, NumberOfEmployees, BillingCountry, OwnerId, Type, Segment__c, Strategic_Flag__c, Owner_Type__c, Navigator_Holdout__c, Navigator_AE_Opt_In__c, IsDeleted, SystemModstamp` |
| Contact | `Id, AccountId, FirstName, LastName, Title, Email, Phone, MailingCountry, HasOptedOutOfEmail, DoNotCall, LinkedIn_URL__c, IsDeleted, SystemModstamp` |
| Opportunity | `Id, AccountId, StageName, IsClosed, IsWon, CloseDate, Loss_Reason__c, OwnerId, CreatedDate, SystemModstamp` |
| Task, Event | Navigator's own plus Nooks and Apollo activity, keyed on `Navigator_Touch_Id__c` |
| User | `Id, Email, Name, ManagerId, Pod__c` (for routing and the manager view) |

## Write (API, from the Slack app and the flows)

| Action | Object | Fields set |
|---|---|---|
| Any send or call | Task | `Subject`, `WhoId`, `WhatId`, `ActivityDate`, `Navigator_Touch_Id__c`, `Navigator_Draft_Id__c`, `Navigator_QA_Grade__c`, `Navigator_Play__c` |
| Intro requested | Task | same, `Subject = "Warm intro requested via <connector>"` |
| Signal routed to AE (open opp) | Task on the opp, assigned to the AE | `Subject = "Navigator signal: <type>"`, description with the quote and receipt URL |
| Customer signal | Note on the account, to the CSM | |
| Meeting booked | Event; Opportunity created at Discovery with `Navigator_Source__c = true`; AE assigned by the existing assignment rule | |
| Disqualify | `Navigator_Disqualified_Until__c`, `Navigator_DQ_Reason__c` | |
| Holdout assignment (once, at pilot start) | `Navigator_Holdout__c` | |

Navigator never changes `OwnerId`, never merges accounts, never deletes.

## Custom fields to create (RevOps, week 1)

`Segment__c` (if not present), `Strategic_Flag__c`, `Owner_Type__c`, `Navigator_Holdout__c`, `Navigator_AE_Opt_In__c`, `Navigator_Touch_Id__c`, `Navigator_Draft_Id__c`, `Navigator_QA_Grade__c`, `Navigator_Play__c`, `Navigator_Source__c`, `Navigator_Disqualified_Until__c`, `Navigator_DQ_Reason__c`, `LinkedIn_URL__c` (if not present), `Pod__c` on User.

## Identity

`Account.Id` maps to `account_id` in `core.account_ids` (`id_type = sfdc_id`). Public accounts map through SteadyBase's `external_id` route; private through `resolve_private`. Duplicates in Salesforce show up as two `sfdc_id`s on one `account_id`, which is reported to RevOps, never merged by Navigator.

## To verify

- [ ] Sandbox access for the `sf` CLI and the connector.
- [ ] Which of the custom fields already exist under other names.
- [ ] The assignment rule for unowned accounts in a territory.
