# LegalEase AI - Core Functionalities & Features

## Overview
LegalEase AI provides a complete end-to-end legal drafting lifecycle. Below is a detailed technical examination of each core capability implemented across the frontend and backend.

---

## 1. Document Type Selection
- Supported categories include:
  1. Employment Contract
  2. Lease Agreement
  3. Non-Disclosure Agreement (NDA)
  4. Service Agreement
  5. Partnership Agreement
  6. Sales Agreement
  7. Freelance Contract
  8. General Agreement
- Built modularly so additional agreement categories can be introduced simply by extending `SUPPORTED_DOC_TYPES` in `backend/config.py`.

## 2. Structured Stakeholder Input
- Captures multiple parties, designations, addresses, and corporate status.
- Example:
  ```text
  Party 1 (Service Provider): Jane Doe, residing at 123 Tech Avenue, Bengaluru, India
  Party 2 (Client): TechNova Solutions Pvt. Ltd., 456 Innovation Park, Mumbai, India
  ```

## 3. Semicolon-Separated Terms & Clauses
- Accepts freeform or bulleted terms separated by semicolons (`;`).
- Enables intuitive drafting without forcing rigid sub-forms for every clause.
- Example:
  ```text
  Payment to be made within 30 days of invoice;
  Provider agrees to deliver work by the agreed deadline;
  Confidentiality must be maintained at all times;
  Either party may terminate with 15 days notice
  ```

## 4. Input & Date Validation
- Evaluates field lengths, non-emptiness, and semantic consistency.
- Date logic enforces that termination or expiration dates cannot precede commencement or execution dates.
- Raises descriptive errors before triggering expensive AI model calls.

## 5. AI Legal Drafting
- Synthesizes user specifications into a formal contract using Google Gemini.
- Incorporates preambles, recitals, definitions, substantive clauses, dispute resolution, governing law, and execution blocks.
- Employs bracketed placeholders (e.g. `[Jurisdiction]`) for omitted jurisdiction-specific items.

## 6. Styled HTML Document Preview
- Renders the generated legal draft inside an elegant dark-mode container.
- Highlights titles, numbered sections, bold keywords, and bullet points.
- Features prominent legal notices and disclaimers.

## 7. Interactive Inline Editing
- Toggled via the **"Click to Edit Document"** button.
- Users can directly adjust text, add clauses, or personalize names in a large text area.
- Clicking **"Save Changes"** updates the application state and re-renders previews and download files instantly.

## 8. Automatic Terms Table Generation
- Parses semicolon-separated terms into clean key-value pairs (e.g. `("Payment", "₹50,000 within 30 days")`).
- Renders **Schedule A: Summary of Agreed Key Terms** across:
  - HTML preview table
  - Microsoft Word (`.docx`) table with slate-navy header shading
  - ReportLab PDF table with alternating row colors and grid borders

## 9. Plain Text (.TXT) Export
- Formatted as clean UTF-8 text.
- Features standardized ASCII borders, document titles, body clauses, structured terms summary, and the legal disclaimer.

## 10. Microsoft Word (.DOCX) Export
- Built using `python-docx`.
- Uses formal legal typography (Times New Roman).
- Embeds organization logo centered in the header.
- Includes numbered headings, left-indented sub-clauses, styled Schedule A table, signature blocks, and running footers.

## 11. Print-Ready PDF (.PDF) Export
- Built with `reportlab`.
- Embeds top branding logo and horizontal accent rules.
- Multi-page canvas automatically stamps running headers, footers, legal disclaimers, and page numbers ("Page X of Y").
- Generates bordered signature lines and date blanks.

## 12. Custom Branding & Logo Support
- Allows users to upload their organization logo (PNG, JPEG, WebP).
- Automatically scales and embeds the logo across DOCX and PDF exports.
- Gracefully falls back to the default LegalEase logo if no custom file is uploaded.
