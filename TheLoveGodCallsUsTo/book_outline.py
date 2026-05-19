"""Book outline for The Love God Calls Us To.

Source of truth for any structural claim verify_counts.py needs to
check: chapter count, attribute-chapter count, attribute count, the
passage range, etc. Keep this in sync whenever the chapter structure
changes.

The book has 14 attribute chapters covering 15 attributes — Chapter 11
takes up the verse-6 contrast pair ("does not rejoice in
unrighteousness, but rejoices with the truth") together as a single
chapter rather than splitting them.
"""

BOOK_OUTLINE = {
    "title": "The Love God Calls Us To",
    "subtitle": "Walking Out 1 Corinthians 13",
    "passage": "1 Corinthians 12:31-13:13",
    "front_matter": [
        "Inscription",
        "Dedication",
        "Preface",
    ],
    "chapters": [
        {"num": 1, "type": "opening",
         "title": "The More Excellent Way",
         "verses": "1 Corinthians 12:31-13:3"},
        {"num": 2, "type": "attribute",
         "title": "Love Is Patient",
         "verses": "1 Corinthians 13:4a",
         "attributes": ["is patient"]},
        {"num": 3, "type": "attribute",
         "title": "Love Is Kind",
         "verses": "1 Corinthians 13:4b",
         "attributes": ["is kind"]},
        {"num": 4, "type": "attribute",
         "title": "Love Is Not Jealous",
         "verses": "1 Corinthians 13:4c",
         "attributes": ["is not jealous"]},
        {"num": 5, "type": "attribute",
         "title": "Love Does Not Brag",
         "verses": "1 Corinthians 13:4d",
         "attributes": ["does not brag"]},
        {"num": 6, "type": "attribute",
         "title": "Love Is Not Arrogant",
         "verses": "1 Corinthians 13:4e",
         "attributes": ["is not arrogant"]},
        {"num": 7, "type": "attribute",
         "title": "Love Does Not Act Unbecomingly",
         "verses": "1 Corinthians 13:5a",
         "attributes": ["does not act unbecomingly"]},
        {"num": 8, "type": "attribute",
         "title": "Love Does Not Seek Its Own",
         "verses": "1 Corinthians 13:5b",
         "attributes": ["does not seek its own"]},
        {"num": 9, "type": "attribute",
         "title": "Love Is Not Provoked",
         "verses": "1 Corinthians 13:5c",
         "attributes": ["is not provoked"]},
        {"num": 10, "type": "attribute",
         "title": "Love Does Not Take Into Account a Wrong Suffered",
         "verses": "1 Corinthians 13:5d",
         "attributes": ["does not take into account a wrong suffered"]},
        {"num": 11, "type": "attribute",
         "title": "Love Does Not Rejoice in Unrighteousness, but Rejoices With the Truth",
         "verses": "1 Corinthians 13:6",
         "attributes": [
             "does not rejoice in unrighteousness",
             "rejoices with the truth",
         ]},  # NOTE: combined verse-6 contrast pair — one chapter, two attributes
        {"num": 12, "type": "attribute",
         "title": "Love Bears All Things",
         "verses": "1 Corinthians 13:7a",
         "attributes": ["bears all things"]},
        {"num": 13, "type": "attribute",
         "title": "Love Believes All Things",
         "verses": "1 Corinthians 13:7b",
         "attributes": ["believes all things"]},
        {"num": 14, "type": "attribute",
         "title": "Love Hopes All Things",
         "verses": "1 Corinthians 13:7c",
         "attributes": ["hopes all things"]},
        {"num": 15, "type": "attribute",
         "title": "Love Endures All Things",
         "verses": "1 Corinthians 13:7d",
         "attributes": ["endures all things"]},
        {"num": 16, "type": "closing",
         "title": "Love Never Fails",
         "verses": "1 Corinthians 13:8-13"},
    ],
    "back_matter": [
        "Appendix A — What It Means to Obey the Gospel",
    ],
}
