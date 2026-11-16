# Website UI research and reference contract

Research date: 16 November 2026. This extends the earlier Streamlit research for a custom localhost website that can later be deployed. It is a curated comparison of relevant real products, not a claim to have found every website or a universal best design.

## What the website can actually show

The product has a trained historical-approval model, the original dataset's input fields, real held-out metrics and CV comparisons, actual SHAP attributions, dataset statistics, and an optional failed cost-policy experiment. It can screen a single application or an uploaded batch and export the resulting predictions.

It does not have customer accounts, a live loan book, processing-time measurements, new bank applications, repayment outcomes, verified credit scores, identity verification, daily activity, or measured savings. A reference's balances, transaction volume, customer logos, avatars, revenue growth or approval queues must not be copied into LoanLens as invented product data.

## Selection

**Primary visual reference: the official [Mercury public product demo](https://demo.mercury.com/dashboard).** This was loaded in Chromium at 1440×1100, its actual application DOM was inspected, and a screenshot was saved and visually reviewed. Unlike a marketing mockup, it exposes the real dashboard shell, navigation, controls, card arrangement and table language without requiring an account. It provides the strongest reproducible visual target among the reviewed references.

**Secondary workflow reference: Blend's [banker application walkthrough](https://help.blend.com/support/solutions/articles/156000319493-banker-experience-with-instant-home-equity).** It shows how lending data is grouped and reviewed. Borrow the grouped intake and contextual review structure, not Blend's brand, legal consent text, credit-pull features or underwriting claims.

Ramp, Stripe and Linear were compared to test that choice. They are supporting evidence rather than separate visual themes to mix into the same interface. Carbon and GOV.UK inform field and error behavior, not the page's look.

## Reference catalogue

| Reference and exact URL | Evidence actually inspected | Useful pattern | Deliberately excluded |
| --- | --- | --- | --- |
| [Mercury product demo](https://demo.mercury.com/dashboard) | Live Chromium page, DOM/computed styles, screenshot `design-references/mercury-demo.png` | Pale narrow navigation, white canvas, compact utility bar, restrained title, action row, bordered panels, tabular numbers | Demo banner, balances, transactions, logos, customer name, proprietary fonts and onboarding overlay |
| [Mercury March 2026 product update](https://mercury.com/blog/march-2026-product-updates) | Primary article plus downloaded/visually inspected Insights and transactions illustrations | Quiet chart color, editable-category vocabulary, restrained supporting text | Marketing growth percentages, decorative trend data, claims about this app having financial integrations |
| [Mercury balances guide](https://support.mercury.com/hc/en-us/articles/28767842120852-Understanding-your-Mercury-balances) | Primary help article | Explain the meaning of a headline number close to that number; distinguish similar concepts | Any suggestion that an approval score is a cash balance or repayment probability |
| [Ramp admin navigation](https://support.ramp.com/ramp-navigation-for-admins/) | Primary guide and downloaded/visually inspected before/after navigation image | Group navigation by task; communicate the current location visibly; short labels with small line icons | Ramp's many products, admin roles, subscriptions and AI services that LoanLens does not implement |
| [Ramp real-time reporting](https://support.ramp.com/real-time-reporting/) | Primary guide and downloaded/visually inspected report/export screenshot | Section title, nearby actions, compact report tabs, export close to the data | Real-time feeds, shared dashboards, scheduled exports or actual company spend claims |
| [Blend banker application walkthrough](https://help.blend.com/support/solutions/articles/156000319493-banker-experience-with-instant-home-equity) | Primary article and downloaded property/applicant UI screenshots | Applicant/property/income groups, adjacent explanation, explicit review outcome | SSN/DOB/address collection, credit pulls, disclosures, identity checks, account creation and actual pre-approval letters |
| [Blend borrower income walkthrough](https://help.blend.com/support/solutions/articles/156000319579-borrower-experience-with-blend-income) | Primary help text and image references | Allow people to review and edit income information; distinguish provided information from an inferred/pre-filled value | Bank/payroll linking and verified-income status, which are not present here |
| [Blend lender tools](https://blend.com/products/mortgage-suite/lender-tools/) | Primary product text, supported by the official mortgage PDF below | Keep review context and loan information in one workspace | Rates, product matching, signatures, credit-provider integrations and lender suitability claims |
| [Stripe Dashboard basics](https://docs.stripe.com/dashboard/basics) | Primary documentation of navigation, reporting, filtering and export | Dedicated sidebar destinations, table/filter/export actions grouped together, important notices near relevant data | Payment products, settings, account administration and notifications without real backend behavior |
| [Linear features](https://linear.app/features) | Primary feature page and public image references; no signed-in app inspected | Clear hierarchy, compact utility controls, consistent workspace language | Dark marketing aesthetic and issue-management features irrelevant to loan screening |
| [Carbon form guidelines](https://www.carbondesignsystem.com/building-blocks/core/components/form/guidelines) | Primary component guidance | Visible labels and helper text, aligned field groups, one clear submit action, loading/error states | IBM branding or a component library dependency for a small native form |
| [GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/) | Primary behavior and example markup | Visible error summary, focus management and links to incorrect fields | Government visual branding and legal-authority cues |

### Additional primary artifacts

- [Official Blend end-to-end mortgage PDF](https://info.blend.com/hubfs/48021128/PDF/Infographic/Meet_Blend_end_to_end_mortgage.pdf), especially the loan-officer toolkit spread: useful evidence that review and supporting information belong in one workspace. It is a 2021 document and is not evidence of the exact current product UI or current results.
- [Inter font license](https://github.com/rsms/inter/blob/master/LICENSE.txt): SIL Open Font License 1.1 verified from the source repository. If self-hosting Inter, retain its license. A system font stack is also suitable and requires no external font request. Mercury's Arcadia font is not copied or distributed.

## Deep inspection: Mercury

The public demo was redirected from `https://demo.mercury.com/` to `/dashboard`. Its demonstration data are the vendor's demo records, not real observations for this college project. The screenshot is a research artifact and must never become an image used to fake LoanLens functionality.

The following are **observed values** from computed styles or bounding boxes at the inspected viewport; they are not guesses from a design gallery:

| Element | Observed value | Intended adaptation |
| --- | --- | --- |
| Main body text | `Arcadia Text`, system UI, sans-serif; `rgb(30, 30, 42)` | Original system/appropriately licensed sans-serif; similarly dark neutral text |
| Page title | `Arcadia Display`; 28px type; 36px line box; weight 380 | Restrained 28–32px page title; do not use a large marketing hero inside the workspace |
| Active Home item | x=8px; width=203px; height=30px; radius=8px | Compact full-width active navigation item, text plus icon and persistent current-page state |
| Active-item fill | `rgba(112, 115, 147, 0.1)` | Low-contrast neutral/lavender selection fill with sufficiently dark text |
| Main content region | x=338.5px; width=968px at a 1440px viewport | Centered bounded workspace after the left rail, rather than edge-to-edge cards |
| Panel label | 15px font; 24px line box; `rgb(54, 54, 68)` | Small readable section labels; stronger numbers; secondary descriptions beneath |
| Header surface | `rgb(255, 255, 255)` | White main surfaces and subtle neutral borders, with color reserved for actions and state |
| Main graph panel | 472×350px, 12px radius, 1px border `rgba(112, 115, 147, 0.1)`, white background | Same quiet panel treatment, with sizing adapted to the actual form/evidence content |
| Graph-panel header inset | `20px 24px 2px` | Consistent 24px panel content inset rather than arbitrary padding on each card |
| Primary Send action | white text on `rgb(82, 102, 235)` (`#5266eb`); 16px type; pill radius `9999px` | A single clear blue-violet primary action, with neutral secondary actions; retain project-specific icon/text |

The rail appears about 219px wide in the screenshot. Full rail geometry is visually observed rather than exhaustively measured. Do not describe approximate observations as exact CSS values. The nested panel and primary action were subsequently measured after waiting for the content, so their listed properties are verified. A second capture closes the public demo's tour overlay for a clearer shell comparison.

Its useful structural relationship is a narrow persistent navigation rail, a thin top utility row, a compact page-heading/action area, then two primary content panels and a denser table beneath. Different LoanLens pages should share that shell, spacing, type scale, border language and active-nav treatment. Use project content and real model evidence in those regions.

## Deep inspection: Ramp

The official current admin guide identifies a navigation update dated November 2026. The inspected image shows task groups separated with fine rules, icons plus short labels, indentation for child destinations, and a pale gray active group. The report screenshot shows a larger report title above a tab strip, an action aligned to the heading, a bordered KPI/report region, and export commands adjacent to that region.

These support a compact functional workspace. Ramp's bright yellow action color is **not** part of the chosen Mercury-based palette. Its collaboration, subscription and AI-chat UI must not be added as dead controls to make this project look busier.

## Deep inspection: Blend

The primary banker guide separates property information, personal information, income, review and completion. It includes a lender-entered path, not just a borrower marketing funnel. The screenshots are an operational form reference and are useful for grouping the model's existing fields and keeping contextual information near the form.

LoanLens needs fewer fields than a mortgage origination system: income, requested loan/term, credit-history indicator, dependents, education, employment and property area. It should not collect names, SSN, phone, addresses, IDs or bank credentials just because Blend does. Optional demographic audit fields must be visibly separated from model inputs. Explanations must identify missing/imputed fields rather than presenting them as verified facts.

## Design contract and matching matrix

“Match” means a recognizably consistent visual system and the same useful hierarchy/density, not a deceptive clone with Mercury branding or another product's data. Every new page should use one visual family. The root implementer should verify this matrix against the reference capture and the final live screenshots.

| Reference pattern | LoanLens implementation target | What to check in the rendered result |
| --- | --- | --- |
| Mercury narrow pale navigation rail | Persistent product mark and real destinations: overview, new assessment, batch screening, model evidence, methodology | Same rail width and visual weight across pages; clear active state; no decorative dead nav items |
| Mercury compact utility/header row | Breadcrumb/current page and concise environment/status text, with actual actions only | Header height stays compact; labels align to content; no fake notification count or invented user profile |
| Mercury restrained title and action row | Task heading, one-line context, primary “New assessment”/“Run assessment” action and contextual secondary action | Fixed type scale; no giant hero; primary action easy to locate |
| Mercury white bordered panels | One dominant assessment form and adjacent review/result area; evidence pages use chart/table panels | Consistent radii, border tone, padding and heading spacing; no unrelated gradients or card styles |
| Mercury numerical hierarchy | Actual held-out metrics or a submitted applicant's model score and active threshold | Tabular numerals, consistent precision and explicit dataset/policy labels; no fabricated activity metrics |
| Mercury table below overview | Actual model comparison table or this session's submitted CSV results | Align numeric columns; retain labels and real counts; scroll the table rather than the whole mobile page |
| Blend grouped input | Financial details, application/property details and separate optional audit fields | Visible labels and units; preserve blank/missing values; no invented default applicant |
| Blend review context | Model suggestion, score, threshold and “Why?” explanation close to the entered details | State in text as well as color; human-review wording; imputation disclosed |
| Ramp report export proximity | CSV template/download beside the batch result table | Actions work and identify their output; no inactive “share” or “schedule” controls |
| Carbon/GOV.UK form behavior | Native keyboard-accessible controls, concise validation, focus to errors, working loading state | Tab through controls; test invalid/empty fields; errors are announced and focus is recoverable |
| Mercury shell adapted to mobile | Rail becomes a usable menu; panels stack and actions wrap | Check 320px, 390px, 768px and desktop widths; avoid horizontal page overflow; keep table overflow local |

The precise project tokens and responsive thresholds are implementation choices, not claimed Mercury CSS. Record their final values next to the matching screenshots when the website is complete.

## Research images and exact provenance

All downloaded images below were visually inspected. They are retained for reference review and attribution, not served as application artwork or copied into production assets.

| Local reference | Exact source |
| --- | --- |
| `design-references/mercury-demo.png` | Chromium screenshot of [the official public demo](https://demo.mercury.com/dashboard), 1440×1100 |
| `design-references/mercury-dashboard-clean.png` | Second Chromium screenshot of [the same official demo](https://demo.mercury.com/dashboard) after dismissing its demo-tour overlay; 1440×1100 |
| `design-references/mercury-insights.webp` | [Official Mercury article asset](https://www.datocms-assets.com/115132/1773686281-2026_blog_messenger-march_insights_1920x1080_2x.webp?auto=format&fit=crop) |
| `design-references/mercury-transactions.webp` | [Official Mercury article asset](https://www.datocms-assets.com/115132/1773686613-2026_blog_messenger-march_auto-cat_1920x1080_2x.webp?auto=format&fit=crop) |
| `design-references/ramp-navigation.webp` | [Official Ramp navigation comparison](https://assets.ramp.com/help-center/ramp-navigation-for-admins/_attachments/ai-spend-navigation-comparison-v2.webp) |
| `design-references/ramp-export.png` | [Official Ramp report export screenshot](https://assets.ramp.com/help-center/real-time-reporting/_attachments/share-export-menu-2026.png) |
| `design-references/blend-property.jpeg` | [Official Blend property-details screenshot](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/156004994760/original/GKG5mqU6K-9Nrdm4-xryHwI1bx7EoiaP6A.jpeg?1744448152=) |
| `design-references/blend-applicant.jpeg` | [Official Blend applicant-information screenshot](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/156004994755/original/gH-35QUQrSA92VbHvxBuYmUGjbKt3Ub8AA.jpeg?1744448050=) |

## Verification limits

- The Mercury demo and the listed screenshots were actually viewed. No signed-in customer account was used. The demo's current interface may change after this research date.
- Marketing artwork is not labeled a full operational dashboard. The Mercury Insights image is a stylized illustration; the Mercury demo screenshot is the primary shell reference.
- The first attempt to measure a nested panel ran before the demo finished rendering; the stable title/navigation measurements above were collected after the page loaded. Unmeasured properties remain labeled approximate.
- Some image URLs timed out in the web reader but downloaded successfully over HTTPS through PowerShell. A guessed Stripe blog URL returned 404 and was replaced by the official Dashboard documentation; it is not used as evidence.
- No source supports copying branding, proprietary fonts, trust badges, fabricated accounts, outside product metrics or claims of lawful credit decisioning into this college project.
- A final visual match and accessibility claim requires inspecting the finished local website. This research document does not itself certify the implementation or a formal WCAG audit.
