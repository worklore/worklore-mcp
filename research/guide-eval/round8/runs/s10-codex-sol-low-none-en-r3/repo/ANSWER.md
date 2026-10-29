# Analytics events implemented

The registration screen sends the five registration events through `Analytics.capture`: the first nonempty edit of each contact field, the selected loan amount when a slider drag ends, each transition to accepted terms, and each enabled Continue tap. Amounts are integers; the Continue event also includes the terms boolean. Email and phone values are never sent.

The offers screen sends `offers_scrolled` with a double scroll offset when the list finishes scrolling beyond its starting position. Existing automatic screen view tracking remains in place.

Verification: `flutter analyze` completed with no issues.
