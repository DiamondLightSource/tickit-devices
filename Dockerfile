FROM registry.hub.docker.com/library/python:3.7-slim AS base

ENV PIP_DEPENDENCIES wheel pipenv
ENV TICKIT_DEVICES_DIR /tickit_devices

#Install git while tickit is a git dependency
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

# Install pip dependencies
RUN rm -rf /usr/bin/python3.7
RUN python3.7 -m pip install --upgrade pip
RUN python3.7 -m pip install ${PIP_DEPENDENCIES}

# Copy tickit code into container
COPY . ${TICKIT_DEVICES_DIR}
WORKDIR ${TICKIT_DEVICES_DIR}

RUN pipenv install --python=python3.7 --system --deploy

##### Runtime Stage ####################################################################
FROM registry.hub.docker.com/library/python:3.7-slim AS runtime

ENV TICKIT_DEVICES_DIR /tickit_devices
WORKDIR ${TICKIT_DEVICES_DIR}

#Install git
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

ENV PYTHON_SITE_PACKAGES /usr/local/lib/python3.7/site-packages

COPY --from=base ${PYTHON_SITE_PACKAGES} ${PYTHON_SITE_PACKAGES}
COPY . ${TICKIT_DEVICES_DIR}

RUN python3.7 -m pip install tickit_devices

CMD ["python3.7", "-m", "tickit"]