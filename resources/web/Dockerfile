FROM ubuntu:trusty
MAINTAINER Ceroic <ops@ceroic.com>

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 627220E7
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates procps python-pip
RUN echo 'deb http://archive.scrapy.org/ubuntu scrapy main' | sudo tee /etc/apt/sources.list.d/scrapy.list
RUN sudo apt-get update && sudo apt-get install -y scrapy scrapyd

# Install some standard libs
RUN pip install requests celery[redis] PyPDF2

# Add our defaults file for increasing file limit
COPY scrapyd /etc/default/

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 6800
CMD ["scrapyd"]
