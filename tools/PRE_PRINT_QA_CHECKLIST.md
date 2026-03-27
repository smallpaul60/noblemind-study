# NobleMind Press — Pre-Print QA Checklist

Run through this checklist before submitting any book for print.

## Content Quality
- [ ] Scripture quotes verified against NASB (`python3 tools/verify_scripture.py BookName`)
- [ ] Language check — no denominational/theological jargon (`python3 tools/check_language.py BookName`)
- [ ] Exegesis verified — all Greek/Hebrew word studies confirmed against Strong's lexicon

## Typographic Quality
- [ ] Orphaned headings check — no section titles stranded at bottom of page
- [ ] Page count verified — matches spine width calculation for cover
- [ ] First/last page check — book starts on recto, no blank pages where there shouldn't be, last page is even (for printing)
- [ ] Font embedding — EB Garamond embedded, no system font fallbacks

## Metadata Accuracy
- [ ] Title page — NobleMind Press, correct author name(s)
- [ ] Copyright page — correct ISBNs (both formats), NASB permission line, correct year
- [ ] Table of Contents — all chapters listed, titles and subtitles match chapter headings
- [ ] Barcode on back cover matches the ISBN for that specific format (paperback ISBN on paperback cover, hardcover ISBN on hardcover cover)
