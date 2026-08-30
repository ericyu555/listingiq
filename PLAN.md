# Ship the hosted version by Fri Sept 4, 2026

Goal: a non-technical seller opens a link, types her store name, and downloads
a CSV. No terminal, no install.

## Her flow (8 steps, only step 8 is scary)

1. Open the link
2. Enter access code
3. Type store name
4. Click Scan
5. Wait ~2 min
6. Review the summary
7. Download the CSV
8. Shopify > Products > Import > tick "overwrite existing products" > upload

Step 8 is where non-technical users quit. OAuth removes it later. For now,
mitigate with numbered instructions and a bold "export a backup first, that
IS your undo."

## Schedule

- [ ] **Sun Aug 30 - deploy first, build nothing.** Push the existing `app.py`
      to Streamlit Community Cloud. Connect the repo, add `ANTHROPIC_API_KEY`
      to their secrets manager, confirm it loads in a browser. ~1 hr.
      *This is the only task with unknown duration. Retire the risk on day one.*
- [ ] **Mon Aug 31** - spot-check ~15 rows of `deliverables/`, send the three
      files to the store owner. Then start the enrichment page. ~1.5 hr.
- [ ] **Tue Sep 1** - enrichment page: store input, progress, summary, samples. ~1.5 hr.
- [ ] **Wed Sep 2** - finish the page, add the access-code gate. ~1.5 hr.
- [ ] **Thu Sep 3** - BUFFER. End-to-end test, write the import instructions. ~1.5 hr.
- [ ] **Fri Sep 4** - ship, text the link.

Thursday is slack, not a work day. A six-day plan with no slack is not a plan.

## Scope is frozen

In: store name input, progress, summary, ten sampled products, CSV download,
access code.

Out: everything else. Ideas that arrive before Friday go in "Later", not in
this build.

## Design notes

**Do not make her review 232 rows.** She won't. Show the patterns instead:
category counts, the size distribution, and ~10 randomly sampled products with
before and after. She approves the shape of the work from ten examples.

**Secrets bridge** so one file works locally and deployed:

```python
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
```

Deployed it reads Streamlit's secrets; locally `st.secrets` is empty and it
falls through to `.env`.

**Access code gate**, because every scan costs ~$3-5 against my own API key and
a public URL with no gate is a bill waiting to happen:

```python
if st.text_input("Access code", type="password") != st.secrets["ACCESS_CODE"]:
    st.stop()
```

**Free tier apps sleep** and take 20-30s to wake. Say so in the UI.

## Later

- **v5, OAuth.** Install once, then 4 clicks: open the app in her Shopify
  sidebar, Scan, review, Apply. No URL, no access code, no CSV, no import
  screen. The handshake is a day; the obligations around it are months
  (Partner account, App Store review, install/uninstall/GDPR webhooks, Billing
  API, an always-on server, token security).
- **v6, webhooks.** Shopify notifies the app when she adds a product, and the
  tags appear on their own. She never opens the app. That is the version people
  pay monthly for.

The progression that matters:

```
today    8 steps, 1 terrifying    she might do it once, as a favour
OAuth    4 clicks, 0 terrifying   she would actually use it
webhook  0 steps                  she would pay for it
```

Going from 8 steps to 4 is not the win. Removing the one step that scares her
is the win.

## Open questions

- **Pricing.** Every scan costs me $3-5. Free trial on N products then paid?
  Per scan? Cannot host publicly without an answer.
- **What to store.** Keeping catalogue data creates a privacy obligation.
  Keeping nothing means no history and no way to measure whether the changes
  worked, which kills outcome tracking.
- **Ask the store owner** whether she would pay for pricing help, while she has
  the tool in hand. Cheapest market research available.
