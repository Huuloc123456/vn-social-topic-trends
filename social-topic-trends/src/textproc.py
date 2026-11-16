"""Text normalisation shared by ETL, training and the dashboard's Text Analyzer.

All functions build Spark column expressions (no Python UDF) so they run in
the JVM, except language detection which needs fastText.
"""
from __future__ import annotations

from pyspark.sql import Column
from pyspark.sql import functions as F

URL_RE = r"(https?://\S+|www\.\S+)"
# Bare domains without a scheme (for example, youtube.com/watch).
DOMAIN_RE = r"\b[\w.-]+\.(com|org|net|app|io|co|social|be|ly|tv|gg|me|uk)\b\S*"
APOSTROPHE_RE = r"['’‘`]"
MENTION_RE = r"@\w+"
HASHTAG_RE = r"#(\w*[\p{L}]\w*)"  # at least one letter: not "#1"


def unescape_html(col: Column) -> Column:
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        col = F.regexp_replace(col, entity, char)
    return col


def extract_hashtags(text: Column) -> Column:
    """Lower-cased hashtags without '#', for example ['congnghe', 'thethao']."""
    return F.array_distinct(F.transform(F.regexp_extract_all(text, F.lit(HASHTAG_RE), 1), F.lower))


def clean_text(text: Column) -> Column:
    """Lowercase, drop URLs/domains/mentions/entities/digits/emoji; join
    contractions (you're -> youre) so they do not split into 're'; keep
    hashtag words."""
    t = unescape_html(F.lower(text))
    t = F.regexp_replace(t, URL_RE, " ")
    t = F.regexp_replace(t, MENTION_RE, " ")
    t = F.regexp_replace(t, DOMAIN_RE, " ")
    t = F.regexp_replace(t, APOSTROPHE_RE, "")
    t = F.regexp_replace(t, r"#", " ")
    t = F.regexp_replace(t, r"[^\p{L}\p{M}\s]", " ")
    t = F.regexp_replace(t, r"\s+", " ")
    return F.trim(t)


def text_for_language(text: Column) -> Column:
    """Text used only for language detection: no URL, mention, hashtag, newline."""
    t = F.regexp_replace(text, URL_RE, " ")
    t = F.regexp_replace(t, MENTION_RE, " ")
    t = F.regexp_replace(t, r"#\w+", " ")
    t = F.regexp_replace(t, r"\s+", " ")
    return F.trim(t)


def normalized_hash(text: Column) -> Column:
    """Hash of the cleaned text, used to find copy-paste / spam duplicates."""
    return F.sha2(clean_text(text), 256)


def is_sensitive(text_clean: Column, hashtags: Column, terms: list[str]) -> Column:
    """Adult / explicit content flag (lexicon match on words or hashtags).
    Used to keep such posts off the projector in presentation mode; the
    posts stay in every statistic."""
    pattern = r"\b(" + "|".join(terms) + r")\b"
    tag_hit = F.exists(hashtags, lambda h: h.isin(terms))
    return F.coalesce(text_clean.rlike(pattern) | tag_hit, F.lit(False))
