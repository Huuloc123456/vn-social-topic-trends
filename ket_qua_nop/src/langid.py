"""Language identification with fastText lid.176 as a pandas UDF (plan 7.5)."""
from __future__ import annotations

import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

LANG_SCHEMA = StructType([StructField("lang", StringType()), StructField("lang_prob", DoubleType())])
MIN_CHARS = 10

_model = None


def _load(model_path: str):
    global _model
    if _model is None:
        import fasttext

        fasttext.FastText.eprint = lambda *a, **k: None  # silence load warning
        _model = fasttext.load_model(model_path)
    return _model


def make_lang_udf(model_path: str):
    @F.pandas_udf(LANG_SCHEMA)
    def detect(texts: pd.Series) -> pd.DataFrame:
        model = _load(model_path)
        langs, probs = [], []
        for text in texts.fillna(""):
            if len(text) < MIN_CHARS:
                langs.append("unknown")
                probs.append(0.0)
                continue
            labels, scores = model.predict(text.replace("\n", " "), k=1)
            langs.append(labels[0].replace("__label__", ""))
            probs.append(float(scores[0]))
        return pd.DataFrame({"lang": langs, "lang_prob": probs})

    return detect
