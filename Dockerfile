FROM registry.hub.docker.com/library/python:3.9 AS base

ENV PIP_DEPENDENCIES wheel pipenv
ENV TICKIT_DEVICES_DIR /tickit_devices

#Install git while tickit is a git dependency
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

# Install pip dependencies
RUN rm -rf /usr/bin/python3.9
RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install ${PIP_DEPENDENCIES}

# Copy tickit code into container
COPY . ${TICKIT_DEVICES_DIR}
WORKDIR ${TICKIT_DEVICES_DIR}

RUN pipenv install --python=python3.9 --system --deploy

##### Runtime Stage ####################################################################
FROM registry.hub.docker.com/library/python:3.9-slim AS runtime

ENV TICKIT_DEVICES_DIR /tickit_devices
WORKDIR ${TICKIT_DEVICES_DIR}

ENV PYTHON_SITE_PACKAGES /usr/local/lib/python3.9/site-packages
COPY --from=base ${PYTHON_SITE_PACKAGES} ${PYTHON_SITE_PACKAGES}

COPY . ${TICKIT_DEVICES_DIR}

CMD ["python3.9", "-m", "tickit"]