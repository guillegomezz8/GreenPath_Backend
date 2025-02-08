# Use an official Python runtime as a parent image
FROM python

# Install PostgreSQL client and development libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /src

# Copy the requirements file into the container
COPY requirements.txt .
COPY docker-entrypoint.sh .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache -r requirements.txt

# Copy the current directory contents into the container at /src
COPY . /src

# Define environment variable
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# # set the docker entry file
# RUN chmod +x docker-entrypoint.sh
# ENTRYPOINT [ "docker-entrypoint.sh" ]
RUN chmod +x ./docker-entrypoint.sh

ENTRYPOINT [ "sh", "./docker-entrypoint.sh" ]

# CMD ["python", "manage.py", "runserver"]
