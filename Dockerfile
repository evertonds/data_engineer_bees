FROM apache/airflow:3.1.6-python3.11

# Set user to root to install system dependencies
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for PySpark
# JAVA_HOME is set in docker-compose.yml for the correct architecture
# This works for both amd64 and arm64

# Download PostgreSQL JDBC driver for PySpark
RUN mkdir -p /opt/airflow/jars && \
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -o /opt/airflow/jars/postgresql-42.6.0.jar && \
    chown airflow:root /opt/airflow/jars/postgresql-42.6.0.jar

# Copy requirements file as root and set permissions
COPY requirements.txt /tmp/requirements.txt
RUN chmod 644 /tmp/requirements.txt && chown airflow:root /tmp/requirements.txt

# Switch back to airflow user
USER airflow

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy project files
COPY --chown=airflow:root src/ /opt/airflow/src/
COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root dbt_project/ /opt/airflow/dbt_project/
COPY --chown=airflow:root great_expectations/ /opt/airflow/great_expectations/
COPY --chown=airflow:root tests/ /opt/airflow/tests/
COPY --chown=airflow:root scripts/ /opt/airflow/scripts/

# Create necessary directories
RUN mkdir -p /opt/airflow/data/bronze/breweries && \
    mkdir -p /opt/airflow/data/silver/breweries && \
    mkdir -p /opt/airflow/data/gold/breweries_by_type_location && \
    mkdir -p /opt/airflow/logs

# Set PYTHONPATH
ENV PYTHONPATH=/opt/airflow:$PYTHONPATH

WORKDIR /opt/airflow
