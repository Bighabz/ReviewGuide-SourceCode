"""
Curated Amazon affiliate links organized by query category.

Each entry maps keyword patterns to a list of real amzn.to short links.
The Amazon provider uses these instead of generating fake mock ASINs.
"""

# Maps (category_keywords) -> list of real affiliate short URLs
# Matching is done by checking if ALL keywords in the key appear in the query
CURATED_LINKS = {
    # Electronics
    "bluetooth speaker": [
        "https://amzn.to/40tnceG",
        "https://amzn.to/4cW8fcm",
        "https://amzn.to/3OE2Rkf",
        "https://amzn.to/4aUTEeI",
        "https://amzn.to/46ZowJS",
        "https://amzn.to/4sflr0x",
    ],
    "noise cancelling headphone": [
        "https://amzn.to/4cg2c2g",
        "https://amzn.to/46sYSNy",
        "https://amzn.to/40hVQbz",
        "https://amzn.to/4qWWrtW",
        "https://amzn.to/4kZCHVl",
    ],
    "laptop student": [
        "https://amzn.to/4tSpXE1",
        "https://amzn.to/3OtNdIf",
        "https://amzn.to/40srrqS",
        "https://amzn.to/3ZTVpE2",
        "https://amzn.to/4kUxiPj",
    ],
    "budget smartphone": [
        "https://amzn.to/40wHa8k",
        "https://amzn.to/4baYypf",
        "https://amzn.to/4s7D16v",
        "https://amzn.to/4ucdsmS",
        "https://amzn.to/4aAkUjS",
    ],
    # Home Appliances
    "robot vacuum pet": [
        "https://amzn.to/4kZU08C",
        "https://amzn.to/3ZYKrNt",
        "https://amzn.to/4cK6Jdq",
        "https://amzn.to/4sxhxAv",
        "https://amzn.to/46qmUst",
    ],
    "washing machine": [
        "https://amzn.to/4u2A4Gq",
        "https://amzn.to/4kXfNxK",
        "https://amzn.to/4qRmimV",
        "https://amzn.to/4siBCKJ",
        "https://amzn.to/4sel4Dv",
    ],
    "dyson shark vacuum": [
        "https://amzn.to/4r3yGk3",
        "https://amzn.to/4s43SQQ",
        "https://amzn.to/4aC3lQt",
        "https://amzn.to/46te6SN",
        "https://amzn.to/4kZFii3",
    ],
    "espresso machine": [
        "https://amzn.to/46NZBZZ",
        "https://amzn.to/4bgoDlV",
        "https://amzn.to/4kVjGTL",
        "https://amzn.to/4rxiqbW",
        "https://amzn.to/4b8KI6O",
    ],
    # Health & Wellness
    "standing desk back": [
        "https://amzn.to/4rHjBWv",
        "https://amzn.to/3ZTY3ts",
        "https://amzn.to/3MTqx3r",
        "https://amzn.to/3ZYlH84",
        "https://amzn.to/3MIFHsr",
    ],
    "supplement weight loss": [
        "https://amzn.to/4baXYIa",
        "https://amzn.to/46OSVuD",
        "https://amzn.to/3OM6Yuw",
        "https://amzn.to/4s88HZr",
        "https://amzn.to/3OBZXg0",
        "https://amzn.to/4cPmL5G",
    ],
    "supplement menopause": [
        "https://amzn.to/4sdlxpu",
        "https://amzn.to/46P16aj",
        "https://amzn.to/46uZPVx",
        "https://amzn.to/4qY1JVW",
        "https://amzn.to/4l0BOf2",
    ],
    "supplement energy focus": [
        "https://amzn.to/4aSaSto",
        "https://amzn.to/4u2BIrA",
        "https://amzn.to/3ZTq1FL",
        "https://amzn.to/4cgr1el",
        "https://amzn.to/4kXo0lz",
    ],
    "massage gun": [
        "https://amzn.to/4kZ7fX1",
        "https://amzn.to/4l2yxMq",
        "https://amzn.to/4tXXqNg",
        "https://amzn.to/4qWfnsA",
        "https://amzn.to/4l0t7kX",
    ],
    "fitness tracker": [
        "https://amzn.to/3ZXGdpy",
        "https://amzn.to/4aRMcBb",
        "https://amzn.to/4scnhiz",
        "https://amzn.to/4tWNnb3",
        "https://amzn.to/46u0M0j",
    ],
    # Outdoor & Fitness
    "hiking boot": [
        "https://amzn.to/4aIxo7G",
        "https://amzn.to/4aU6jP2",
        "https://amzn.to/3MvKUUr",
        "https://amzn.to/3OAEGDf",
        "https://amzn.to/3P2NBNS",
    ],
    "flat feet shoe": [
        "https://amzn.to/3P4MahS",
        "https://amzn.to/3MvLcdZ",
        "https://amzn.to/4si597f",
        "https://amzn.to/47ebcRY",
        "https://amzn.to/3ZYOMQL",
    ],
    "garmin apple watch fitness": [
        "https://amzn.to/46rIc94",
        "https://amzn.to/4tXZNQ5",
        "https://amzn.to/4rFsj7D",
        "https://amzn.to/4l6ws1R",
        "https://amzn.to/4tWPfAB",
    ],
    "treadmill": [
        "https://amzn.to/4aC70hb",
        "https://amzn.to/4siFxXX",
        "https://amzn.to/46pe8uP",
        "https://amzn.to/46VPrGw",
        "https://amzn.to/4qX2ZJ2",
    ],
    # Fashion
    "white sneaker": [
        "https://amzn.to/3ZXKuJu",
        "https://amzn.to/476uRmL",
        "https://amzn.to/4cguOZg",
        "https://amzn.to/4rE2h4J",
        "https://amzn.to/4qX1Hh0",
    ],
    "jewellery tarnish": [
        "https://amzn.to/3MKtN1c",
        "https://amzn.to/4rHcIo2",
        "https://amzn.to/46vziY9",
        "https://amzn.to/4l6BoUr",
        "https://amzn.to/4aXQ2Jb",
    ],
    "streetwear": [
        "https://amzn.to/3OyKi0U",
        "https://amzn.to/3ZYtGly",
        "https://amzn.to/40wRNYM",
        "https://amzn.to/4shzrHk",
        "https://amzn.to/4sezXWl",
    ],
    "watch under 500": [
        "https://amzn.to/4aN66gE",
        "https://amzn.to/3N5VIsv",
        "https://amzn.to/4qX2XAK",
        "https://amzn.to/4aXQTJN",
        "https://amzn.to/4qU4Tdh",
    ],
    "big tall clothing": [
        "https://amzn.to/4cbMKnN",
        "https://amzn.to/3MwIkO1",
        "https://amzn.to/401kjl9",
        "https://amzn.to/4bcefMY",
        "https://amzn.to/4seDT9z",
        "https://amzn.to/4aEwmLq",
    ],
    # Smart Home
    "alexa smart": [
        "https://amzn.to/4l2GelM",
        "https://amzn.to/4r3IWsz",
        "https://amzn.to/3OPqRRr",
        "https://amzn.to/46Y9EeO",
        "https://amzn.to/4sg5N5d",
        "https://amzn.to/4qTKyov",
        "https://amzn.to/3P2VD9u",
    ],
    # Kids & Baby
    "toy 2026": [
        "https://amzn.to/4u2gfis",
        "https://amzn.to/4qX4iHM",
        "https://amzn.to/4rzKtHH",
        "https://amzn.to/3ZXSWZk",
        "https://amzn.to/4cgFw1Y",
        "https://amzn.to/4r3JVcf",
        "https://amzn.to/4sdnEd0",
        "https://amzn.to/3MwI5CB",
    ],
    "baby essential": [
        "https://amzn.to/40y4ZfW",
        "https://amzn.to/46pFVLM",
        "https://amzn.to/4kTSBjM",
        "https://amzn.to/4kU8p68",
        "https://amzn.to/4cOOKT6",
        "https://amzn.to/4l08rtk",
        "https://amzn.to/4qTLWHL",
    ],
}


def find_curated_links(query: str) -> list[str] | None:
    """
    Find curated Amazon links matching a query.

    Returns list of amzn.to URLs if a match is found, None otherwise.
    Matching: all keywords in the key must appear in the lowered query.
    """
    query_lower = query.lower()

    best_match = None
    best_score = 0

    for key_phrase, links in CURATED_LINKS.items():
        keywords = key_phrase.split()
        # Check if ALL keywords in the key appear in the query
        if all(kw in query_lower for kw in keywords):
            # Score by number of matching keywords (more specific = better)
            score = len(keywords)
            if score > best_score:
                best_score = score
                best_match = links

    return best_match
