FROM python:3.9
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install pandas

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    libblas-dev \
    liblapack-dev \
    gfortran \
    libfreetype6-dev \
    libpng-dev \
    pkg-config
    
COPY . /code/
CMD ["/code/wait.sh", "db", "python", "manage.py", "runserver", "0.0.0.0:8000"]


