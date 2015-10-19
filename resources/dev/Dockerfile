# Use phusion/baseimage as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/baseimage-docker/blob/master/Changelog.md for
# a list of version numbers.
FROM phusion/baseimage:0.9.17

# Use baseimage-docker's init system.

# Using https://hub.docker.com/r/phusion/baseimage/
CMD ["/sbin/my_init"]

# ...put your own build instructions here...

# Enabling ssh
RUN rm -f /etc/service/sshd/down
# Enable insecure key
RUN /usr/sbin/enable_insecure_key


# -- From https://hub.docker.com/r/ceroic/scrapyd/~/dockerfile/
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 627220E7
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates procps python-pip
RUN echo 'deb http://archive.scrapy.org/ubuntu scrapy main' | sudo tee /etc/apt/sources.list.d/scrapy.list
RUN sudo apt-get update && sudo apt-get install -y scrapy-0.24 scrapyd

# -- Some utils
RUN apt-get -y install curl apache2-utils

# Install some standard libs
RUN pip install requests celery[redis] PyPDF2 treq

# Add our defaults file for increasing file limit
COPY scrapyd /etc/default/

EXPOSE 6800


# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
