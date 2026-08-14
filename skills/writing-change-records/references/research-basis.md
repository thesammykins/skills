# Research Basis

## Scope

This skill was derived from the supplied `writing-prs` bundle and checked
against its source catalogue. The bundle's draft was treated as a hypothesis,
not copied as the operating contract.

Commit-specific guidance was added from sources available by 31 December 2022.
No post-2022 convention is used as historical support.

The bundle also covered review-comment wording and responding to review. Those
topics were deliberately left out because this skill owns commit and PR records,
not code-review behavior. The retained material is the portion that directly
supports durable change writing.

## Synthesis

The common pre-2023 principle is:

> A change message is a durable engineering record, not a transcription of the
> diff or the author's activity log.

The source code records implementation. Commit and PR prose should preserve the
context that code does not reliably retain: the prior problem, intended outcome,
constraints, important decisions, evidence, and material consequences.

This yields four operating rules:

1. **Write for a future engineer without conversational memory.** A ticket or
   chat link is supplemental, not a substitute for context.
2. **Keep one coherent decision per change.** Description length cannot repair
   scope that is difficult to review or revert.
3. **Scale detail to consequence and review burden.** Small, low-risk changes
   need little prose; short security, migration, or compatibility changes may
   need substantial reasoning.
4. **Treat validation as evidence, not ceremony.** Name what an observed check
   established. Tool and command lists alone do not explain correctness.

The quick/standard/major model is a synthesis from the bundle rather than a
taxonomy asserted verbatim by one source. It operationalizes the older guidance
to keep changes small, explain what and why, review major design before details,
and communicate enough context for the change at hand.

## Primary sources

### Git project — `SubmittingPatches` at v2.38.2

- Historical version: December 2022
- URL:
  https://github.com/git/git/blob/v2.38.2/Documentation/SubmittingPatches
- Supports:
  - separate commits for logically separate changes;
  - a short subject and meaningful body;
  - explaining the existing problem, why the result is better, and discarded
    alternatives when relevant;
  - imperative wording;
  - self-contained context rather than dependence on external discussions.

The historical tag is intentional. Current Git documentation contains later
material and should not be used to backfill this pre-2023 basis without checking
when specific wording appeared.

### Google Engineering Practices — Writing good CL descriptions

- Publicly released as part of the Engineering Practices documentation: 2019
- URL:
  https://google.github.io/eng-practices/review/developer/cl-descriptions.html
- Supports:
  - a change description as a permanent version-control record;
  - a standalone first line;
  - communicating what and why;
  - recording decisions not visible in source;
  - context even for small changes;
  - checking that the final description still matches the change.

Google defines a CL as a self-contained change also called a change, patch, or
pull request, so this guidance applies to both commit-like records and PRs.

### Chris Beams — How to Write a Git Commit Message

- Published: 31 August 2014
- URL: https://cbea.ms/git-commit/
- Supports:
  - subject/body separation;
  - concise imperative subjects;
  - using the body for what and why rather than a code walkthrough;
  - reducing future context reconstruction;
  - omitting the body for an obvious tiny change.

Its 50/72-character conventions are useful defaults, not universal policy;
repository convention takes precedence in this skill.

### GitHub — How to write the perfect pull request

- Author: Keavy McMinn
- Published: 21 January 2015
- Updated: 6 December 2022
- URL:
  https://github.blog/developer-skills/github/how-to-write-the-perfect-pull-request/
- Supports:
  - including purpose and historical context;
  - writing for readers beyond the current participants;
  - saying which feedback is wanted;
  - making work-in-progress state explicit.

### Google Engineering Practices — Small CLs and review navigation

- Publicly released: 2019
- URLs:
  - https://google.github.io/eng-practices/review/developer/small-cls.html
  - https://google.github.io/eng-practices/review/reviewer/navigate.html
- Supports:
  - small, self-contained changes as easier to understand, review, refine, and
    roll back;
  - examining major design and the most important part of a change before local
    detail;
  - splitting changes that are too large to understand.

### GitHub — Issue and Pull Request templates

- Published: 17 February 2016
- URL:
  https://github.blog/developer-skills/github/issue-and-pull-request-templates/
- Supports templates as prompts that prevent missing information. The skill's
  rejection of empty headings and ceremonial `N/A` fields is a synthesis: a
  template serves the record, not the reverse.

## Empirical support retained from the bundle

### Sadowski et al. — Modern Code Review: A Case Study at Google

- ICSE 2018
- URL:
  https://research.google/pubs/modern-code-review-a-case-study-at-google/
- Evidence base: 12 interviews, 44 survey respondents, and review logs for nine
  million changes.
- Supports lightweight modern code review as an engineering process and the
  value of reviewable changes.

### Bosu, Greiler, and Bird — Characteristics of Useful Code Reviews

- MSR 2015
- URL:
  https://www.microsoft.com/en-us/research/publication/characteristics-of-useful-code-reviews-an-empirical-study-at-microsoft/
- Evidence base: roughly 1.5 million review comments from five Microsoft
  projects.
- Supports the importance of change and review context to useful feedback.

### Gousios et al. — Work Practices and Challenges in Pull-Based Development

- ICSE 2015
- URL: https://gousios.org/bibliography/GZSD15.html
- Evidence base: survey of 749 integrators plus quantitative project data.
- Supports tests and code review as important inputs to judging contribution
  quality.

## Evidence and automation context retained from the bundle

- GitHub, *Clearer mergability information for Pull Requests* (20 July 2015):
  https://github.blog/news-insights/clearer-mergability-information-for-pull-requests/
- GitHub, *Protected branches and required status checks* (3 September 2015):
  https://github.blog/news-insights/product-news/protected-branches-and-required-status-checks/

These establish that automated checks were already merge-readiness inputs. The
skill's distinction is that status checks support a claim but do not replace the
engineering explanation of what changed or why it is acceptable.

## Source rule for future edits

When changing the historical basis:

1. Prefer contemporary primary guidance or original research.
2. For this pre-2023 framing, reject sources first published after 31 December
   2022.
3. For a live page, verify that the specific practice existed before the cutoff
   where feasible.
4. Record what operational rule the source actually supports.
5. Do not import current AI-generated PR conventions merely because they are
   common now.
