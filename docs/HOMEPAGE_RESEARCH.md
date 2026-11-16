# Mortgage homepage research and LoanLens direction

Research date: 16 November 2026. This report supports the new public-facing home page at `/` and the connected screening workspace. It supplements `WEBSITE_REFERENCES.md`, whose Mercury references are useful for dense application screens but do not provide the right home-buying introduction.

## Recommendation

Use **Better Mortgage as the primary colour and hierarchy reference**, with **Blend's split copy/product composition**. Build an original warm ivory, forest-green home page around a house illustration and a clear route into the working screening tool. Carry the same typography, navigation, buttons and surfaces into the workspace. The result should feel like one housing product, with a welcoming introduction followed by useful tools.

This is an adaptation of observable design patterns, not a brand clone. Better currently markets an AI chat experience; LoanLens should introduce the prediction and explanation features it actually implements. A restrained editorial display face would be a deliberate LoanLens choice: Better's inspected face was a sans-serif, not an editorial serif.

## Sources and evidence

Seven current primary sources were consulted. All source claims belong to those companies and are not evidence of LoanLens performance.

| Reference | Exact source | Evidence collected | Useful pattern |
| --- | --- | --- | --- |
| Better Mortgage | https://better.com/ | Live browser, HTTP 200, desktop screenshots, computed heading/action styles | Deep forest hero, high contrast headline, warm ivory supporting surface, simple pill actions |
| Blend | https://blend.com/ | Live browser, HTTP 200, desktop screenshots, computed styles, below-fold capture | Split hero with application visuals, primary/secondary CTA pair, product-to-proof-to-resources progression |
| Habito | https://www.habito.com/ | Live browser, HTTP 200, desktop screenshots, computed styles; consent declined and animation paused | Friendly home-buying intent, two clear journeys, numbered explanation, discoverable motion control |
| Figure | https://www.figure.com/ | Live browser, HTTP 200, desktop screenshot and computed styles | Clear grouping of product capabilities, short heading and descriptive subheading, modular sections |
| Better.co.uk | https://www.better.co.uk/ | Live browser screenshot; main content rendered, account area still loading | Cream canvas, spacious central mortgage message, strong two-action hierarchy, surrounding decorative objects |
| Upstart | https://www.upstart.com/ | Public page text via web retrieval; browser returned HTTP 403 challenge | Text-level comparison: direct loan intent and an action with nearby qualification copy |
| Rocket Mortgage | https://www.rocketmortgage.com/ | Public page text via web retrieval; browser returned HTTP 403 | Text-level comparison: buying/refinancing journey navigation and resources |

Upstart and Rocket were **not visually inspected**: challenge/error screens are not representative UI. No bypass was attempted, and those error captures were removed. Better.co.uk is separate from the US Better reference; the visual relationship here is a comparison, not a claim of shared product behaviour.

## Capture method and provenance

Screenshots were captured from the actual primary URLs with Chromium through the installed Playwright 1.65.2 tool using `uv tool run --from playwright python`. The desktop viewport was **1440 × 1000 CSS pixels**. Pages were allowed approximately three seconds after DOM content loaded; asynchronous content and animation can change the result.

The detailed measurements below were read with the browser's `getComputedStyle()` and `getBoundingClientRect()` from visible headings, actions and ancestor surfaces at that viewport. Values describe that captured desktop state, not a complete responsive design system. Pixel positions are evidence of that state, not a requirement to reproduce them.

The clean captures declined available consent banners using the sites' own controls: Better opt-out, Blend deny and Habito reject-all. Habito's built-in background-animation control was paused before the clean capture. Figure's initial capture retains its cookie panel. Better.co.uk's navigation account area retained a loading indicator; the screenshot should not be treated as evidence of a fully settled account flow.

Useful files, relative to this document:

- `design-references/homepage-better-clean.png`: full initial desktop viewport after consent choice.
- `design-references/homepage-blend-clean.png`: split hero after consent choice.
- `design-references/homepage-blend-progression.png`: lower viewport after an 850px scroll.
- `design-references/homepage-habito-clean.png`: consent dismissed and animation paused.
- `design-references/homepage-habito-progression.png`: numbered explanatory section.
- `design-references/homepage-figure.png`: modular product layout; cookie panel visible.
- `design-references/homepage-better-uk-clean.png`: cream central hero and two journeys.

The additional `homepage-*-sections.png` and initial `homepage-*.png` files preserve earlier viewport states. Screenshots are research records; they must not become LoanLens's in-product illustrations or pretend to show its own UI.

## Deep inspection: Better Mortgage

Better's live page now leads with Betsy AI and a central chat surface. Its hero uses a dark forest background and a large centred headline. The navbar is unusually quiet relative to the headline; the principal action remains easy to identify. The warm ivory surrounding surface prevents the whole product from feeling like a dark analytics dashboard.

| Measured element | Observed value |
| --- | --- |
| Hero ancestor background | `rgb(7, 49, 38)` / `#073126` |
| Surrounding page surface | `rgb(255, 253, 250)` / `#fffdfa` |
| Main heading | Proprietary `betterSans`; 72px size, 72px line height, weight 500, white |
| Heading bounds | x=56px, y=168px, width=1328px, height=144px |
| Main header action | 130.31px × 48px; 16px text / 24px line height; weight 700 |
| Main header action fill | `rgb(1, 120, 72)` / `#017848` |
| Action corner radius | 9999px (pill treatment) |
| Navigation text | 16px / 24px with 48px-high action boxes |

**Use:** the forest/ivory relationship, uncluttered navigation, oversized promise, rounded primary action and product surface that explains what happens next.

**Adapt:** a split hero suits LoanLens's original house illustration and explanation preview better than copying Better's current centred chat. The CTA must open the real screening form. A secondary action can scroll to how the model works or open the workspace. Do not reproduce Better's chatbot, customer/funding counters, partner logos, pricing promises or third-party trust badges.

## Deep inspection: Blend

Blend separates a left-aligned headline and short copy from a larger visual field of layered financial-product screens. The contrast between human-readable introduction and concrete application UI is a useful bridge from a marketing home page into LoanLens's existing tools. Its main and secondary hero actions sit together, and the below-fold narrative broadens from the product to applications and resources.

| Measured element | Observed value |
| --- | --- |
| Main heading font | `Untitled Sans`, Helvetica, Arial, sans-serif |
| Heading typography | 52px size, 57.2px line height, weight 300, `#333333` |
| Heading bounds | x=66px, y=236.59px, width=445px, height=171.61px |
| Hero primary action bounds | x=66px, y=522.20px, width=158.41px, height=41.19px |
| Hero action text | Approximately 16px / 19.2px, weight 500 |
| Hero button corners | 12px |
| Header primary action | 170.66px × 54px, radius 12px |

The inspected anchor itself returned a transparent background for some actions because the visible fill belongs to nested styling. Its blue appearance is visually confirmed; an exact CTA blue is deliberately not reported as a computed anchor token.

**Use:** balanced split hero, a small amount of supporting copy, clear CTA contrast and a product-specific visual. The observed sequence of product offering, use cases, customer proof, resources and final action can become an honest project sequence: screening, explanation, methodology, model evidence and a final tool entry.

**Adapt:** use forest/ivory instead of Blend's blue/mint palette. Show a house illustration and real prediction/explanation UI, with any static decorative example explicitly labelled. Do not import its ROI claims, partner list, mortgage figures or customer outcomes. Approximate visual proportions are layout inspiration, not measured CSS grid tracks.

## Deep inspection: Habito

Habito is the strongest reference for immediately making the subject feel like home buying rather than generic banking software. The current site displays Habito by Monzo branding, a colourful illustrated scene, a pale rounded central text panel and two prominent user journeys. The following section starts a numbered explanation. The design has a built-in animation pause control.

| Measured element | Observed value |
| --- | --- |
| Main heading font | `RightGrotesk`, Impact, sans-serif |
| Heading typography | 80px size, 88px line height, weight 400, `#222222` |
| Heading bounds | x=481.97px, y=226px, width=476px, height=176px |
| Measured hero ancestor colour | `rgb(150, 160, 255)` / `#96a0ff` beneath the changing artwork |
| Body/control font | `Roobert`, Trebuchet, Helvetica, sans-serif |
| Header primary action | 154.75px × 56px; 16px / 24px, weight 700; radius 32px |
| Header action fill | `#151515` |
| Hero journey actions | Approximately 224px wide × 56px high; blue `#006be6`; radius 32px |

**Use:** understandable journey choices, a housing-specific visual, numbered process, explanatory tone and a way to avoid distracting motion.

**Adapt:** LoanLens should retain the calmer forest/cream identity. It does not need Habito's loud purple scene, animation, proprietary typefaces, mortgage advisory wording or ratings. The useful second journey is model/workspace exploration, since this project does not offer refinancing.

## Additional visual comparisons

**Figure:** a 60px/60px, weight-400 Instrument Sans heading (`#1a1b22`) sits above a clearly grouped product grid. Its primary header action is 218.27px × 50px with 18px/28px text and a pill radius. This is useful evidence for clean feature grouping and readable CTA scale. Its crypto products, rates, funding times and financial offers are outside LoanLens's purpose.

**Better.co.uk:** the captured ivory hero gives the message substantial breathing space, places two journey buttons directly beneath it and keeps decorative objects at the edges. It supports a warm home-buying tone. Do not copy its review row, customer count/savings assertions, financial reassurance or object assets. Exact type and colour tokens were not measured for this page; the description is visual observation only.

## LoanLens translation: an actual home page

| Home-page element | Reference basis | LoanLens implementation decision |
| --- | --- | --- |
| Header | Better's quiet navigation; direct journey links across mortgage sites | Original LoanLens identity, page anchors, workspace entry and one primary screening action |
| Hero | Better's colour/hierarchy; Blend's split layout; mortgage-specific art from Habito | Warm ivory and forest panel, concise housing-screening headline, short explanation, original illustration, primary screening CTA and secondary walkthrough |
| Evidence strip | Clear financial-product proof hierarchy | Only dataset/model values loaded from actual project outputs; show labels and context, never pretend these are customer outcomes |
| Three-step process | Habito's numbered explanation | Enter application details; run the trained model; review probability and SHAP reasons |
| Explainability section | Blend's application visual beside explanation | Actual SHAP/prediction capability with plain-English descriptions; distinguish historical approval probability from repayment/default probability |
| Capability grouping | Figure's clear modules | Individual screening, batch CSV screening and model evidence, each linked to a working route |
| Methodology / evidence | Blend's progression into supporting material | Source dataset, split/CV methodology, limitations and existing metrics rather than generic sales claims |
| FAQ | Common lending-site explanation pattern | Explain approval prediction, model limitations, SHAP, data source and the educational scope |
| Final action and footer | Repeated entry point on real lending pages | Return to the real form, workspace and documentation; no unimplemented login or newsletter controls |

The workspace should retain its useful data density, but share the home page's logo, forest accents, restrained borders, typography and button hierarchy. Returning home and locating the workspace must remain obvious on every route.

### Proposed project tokens, not copied measurements

These are implementation choices to create consistency, not claims about reference CSS:

- Use the measured Better forest `#073126` and green `#017848` as reference points, with a warm ivory base near `#fffdfa`; independently verify text contrast.
- Use an available licensed display face only if it improves housing/editorial tone; pair it with one readable sans-serif. Do not download proprietary reference fonts.
- Aim for roughly 56–72px desktop hero type and 32–44px on narrow screens, adjusting to real wrapping. Body text should remain comfortably readable around 16px or larger.
- Use an approximately 1200–1280px content container, generous section spacing and a consistent spacing scale. These widths are project choices.
- Keep primary actions easy to tap, with visible keyboard focus. Collapse the hero to a meaningful text-first mobile order; decorative art must not push the first CTA out of reach.
- Prefer static art and subtle CSS transitions. Respect `prefers-reduced-motion`; do not add animation only because a reference has it.

## Content integrity and asset use

LoanLens predicts labels from a historical loan-approval dataset. The site must not claim to predict repayment/default, guarantee bank approval, represent a lender or demonstrate verified business impact. Reported test performance needs its sample size and evaluation context. Approval probability should be described as the model's estimate, not the chance of receiving a real mortgage.

Illustrative house art may be original AI-generated artwork, but should not be presented as a real funded property, real customer or evidence of model quality. Static screen previews must not fabricate applicant results. Reference screenshots, names and trademarks remain research attribution; they are not production product assets. No copied testimonials, star ratings, press logos, lender logos, review counts, advertised rates, approval times or savings statistics should appear.

## Verification boundaries

This research verified live desktop rendering for Better, Blend, Habito, Figure and Better.co.uk and inspected the saved screenshots. It did not conduct a mobile reference audit, authenticate to lender accounts, submit applications or test those companies' financial flows. Two source sites blocked browser rendering, and Better.co.uk retained a loading indicator in its account area.

The final LoanLens implementation still requires its own desktop/mobile screenshot review, keyboard/navigation checks, contrast checks, working-route checks and prediction/API validation. This report does not claim those app checks have passed.

