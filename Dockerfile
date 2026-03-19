FROM python:3.11

RUN apt-get update && apt-get install -y \
    binutils \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    postgresql-client \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY requirements.txt .
COPY docker-entrypoint.sh .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /src

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN chmod +x ./docker-entrypoint.sh
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
