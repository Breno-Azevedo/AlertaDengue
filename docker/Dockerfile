FROM condaforge/mambaforge

RUN apt-get -qq update --yes \
  && apt-get -qq install --yes --no-install-recommends \
  build-essential git make postgresql-client \
  ca-certificates wget locales cron \
  && rm -rf /var/lib/apt/lists/*

#Set locale
RUN sed -i -e "s/# pt_BR.*/pt_BR.UTF-8 UTF-8/" /etc/locale.gen \
  && dpkg-reconfigure --frontend=noninteractive locales

# Copy environment file to tmp/
ARG PYTHON_VERSION
COPY environment-${PYTHON_VERSION}.yml /tmp/environment.yml

# Use environment to update the env base
RUN conda update -n base -c defaults conda \
  && conda install mamba -n base -c conda-forge \
  && mamba update --all --yes --quiet \
  && mamba env update --file /tmp/environment.yml --name base \
  && mamba clean -afy

# Create deploy user
ARG HOST_UID
ARG HOST_GID
COPY docker/prepare_permission.sh /prepare_permission.sh
RUN /prepare_permission.sh

## Copy code to the container with permissions to user
COPY --chown=deploy:deploy AlertaDengue  /srv/deploy/AlertaDengue
COPY --chown=deploy:deploy requirements.txt example_env_file /srv/deploy/

RUN mkdir /srv/deploy/logs \
  && chown -R deploy:deploy /srv/deploy/logs

RUN cp -p /srv/deploy/example_env_file /srv/deploy/.env

# Create script activate environment
RUN echo 'source /opt/conda/bin/activate base && exec "$@"' > activate.sh
RUN chmod +x /activate.sh
WORKDIR /srv/deploy/AlertaDengue

# Configure cron for DBF request
COPY docker/cron-tasks /etc/cron.d/cron-tasks
RUN chmod 0644 /etc/cron.d/cron-tasks \
  && crontab -u deploy /etc/cron.d/cron-tasks \
  && echo "deploy"  > /etc/cron.allow \
  && touch /var/log/cron.log \
  && chown deploy:deploy /var/log/cron.log

ADD docker/entrypoint.sh /entrypoint.sh

# USER deploy

ENTRYPOINT ["bash", "/activate.sh"]
CMD ["/entrypoint.sh", "/srv/deploy/AlertaDengue/runwsgi.sh"]
