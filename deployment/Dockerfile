#
# BUILD STEP: 
# Pull the base image
#
FROM ubuntu:groovy-20200723 as base_image
USER root
# Create a working user
RUN addgroup -gid 1000 app
RUN adduser -uid 1000 -gid 1000 \
    --disabled-password \
    # --no-create-home \
    --gecos '' \
    app

#
# BUILD STEP: 
# Python image from base linux image
#
FROM base_image as python_image
ENV PYTHON_VERSION 3.8
# Install Python and pip
RUN apt-get update && \
    apt-get install -y \
    --no-install-recommends \
    python$PYTHON_VERSION python3-pip python3-setuptools \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Make some useful symlinks that are expected to exist
RUN ln -s /usr/bin/python$PYTHON_VERSION /usr/bin/python
# Upgrade PIP
RUN pip install --upgrade pip


#
# BUILD STEP: 
# Install setup tools
#
FROM python_image as pip_tools
RUN pip install pip-tools


#
# BUILD STEP: 
# Build linting image
#
FROM python_image as linting_image
RUN pip install flake8

#
# BUILD STEP: 
# Install python requirements for prod
#
FROM python_image as prod_requirements
WORKDIR /code
COPY requirements/app_requirements.txt requirements/
RUN pip install -r requirements/app_requirements.txt

#
# BUILD STEP: 
# Build image for prod
#
FROM prod_requirements as prod_image
RUN chown -R app:app /code
RUN chown -R app:app /var/log
USER app
WORKDIR /code
COPY . .
ENV PYTHONPATH=.
CMD [ "python", "src/main.py" ]

#
# BUILD STEP: 
# Build image for dev
#
FROM prod_requirements as dev_image

USER root
RUN apt-get update && \
    apt-get install -y \
    --no-install-recommends \
    sudo vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/dev_requirements.txt requirements/
RUN pip install -r requirements/dev_requirements.txt

RUN chown -R app:app /code
RUN chown -R app:app /var/log
USER app
COPY . /code
CMD [ "python", "src/main.py" ]