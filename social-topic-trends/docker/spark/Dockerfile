# One image for Spark master, workers, the job client and the dashboard,
# so driver and executors always share the same Spark, Python and libraries.
FROM apache/spark:3.5.3-scala2.12-java17-python3-ubuntu

USER root

COPY requirements-spark.txt /tmp/requirements-spark.txt
RUN pip install --no-cache-dir -r /tmp/requirements-spark.txt \
 && mkdir -p /opt/models \
 && curl -fsSL -o /opt/models/lid.176.ftz \
      https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

ENV PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3 \
    PYTHONPATH=/app:/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.7-src.zip \
    PATH="/opt/spark/bin:/opt/spark/sbin:${PATH}"

WORKDIR /app
