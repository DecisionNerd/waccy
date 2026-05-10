# WACCY Mission

WACCY exists to make institutional-quality financial modeling accessible to small businesses and the people who advise, invest in, lend to, or operate them.

Small businesses often have the same strategic questions as larger companies:

- What is this business worth?
- What is actually driving cash flow?
- How risky is growth, debt, or a transaction?
- Which financial records can be trusted, and which need review?
- How does this business compare with better-documented peers?

But their records are usually messier. QuickBooks accounts may be inconsistent, transactions may be misclassified, historical data may be incomplete, and personal, operational, and financing activity may be blended together. WACCY's mission is to turn that imperfect source data into auditable, decision-ready financial models without pretending the data is cleaner than it is.

## Core Thesis

Financial modeling quality depends on classification quality. A beautiful model built on misclassified accounts is still wrong.

WACCY therefore starts with a standardized financial ontology, maps all source data into that ontology, reports confidence and data quality, and only then builds financial statements and models. The platform should be skeptical of source classifications, transparent about assumptions, and explicit about gaps.

## Who It Serves

WACCY is designed primarily for:

- advisors, accountants, investors, lenders, and operators working with small businesses
- founders and owners who need clearer financial visibility
- developers building financial-modeling workflows on top of messy business data

The platform is not designed to exclude larger companies, but its center of gravity is the small-business world: companies that need rigorous analysis but often lack rigorous financial infrastructure.

## How WACCY Should Work

WACCY should prefer deterministic, reproducible logic wherever possible:

- parse structured data with structured parsers
- map known accounts and concepts with explicit rules
- calculate financial statements with transparent formulas
- validate outputs with reconciliation checks

LLMs and foundation models can help when ambiguity is real: messy account names, incomplete context, document interpretation, and classification uncertainty. They should assist classification and interpretation, not become a black box for financial calculations.

## Long-Term Vision

WACCY should become a standard open platform for automated financial modeling from imperfect business records. Over time, it should support extraction from accounting systems, public filings, documents, banking systems, CRMs, payroll systems, and other operational sources, while maintaining a consistent ontology and auditable modeling layer.

The long-term goal is simple: users should spend less time wrestling with incomplete records and more time making informed decisions.

## Where Details Live

This mission document intentionally stays high-level. The detailed product, modeling, and technical commitments live in:

- [1-EXPERIENCE.md](1-EXPERIENCE.md): user workflows, diagnostics, and release experience
- [2-REQUIREMENTS.md](2-REQUIREMENTS.md): financial modeling requirements and roadmap
- [3-ARCHITECTURE.md](3-ARCHITECTURE.md): data-source strategy, ontology, extensions, and implementation design
