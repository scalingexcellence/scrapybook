Learning Scrapy Book
==========

This book covers the long awaited Scrapy v 1.0 that empowers you to extract useful data from virtually any source with very little effort. It starts off by explaining the fundamentals of Scrapy framework, followed by a thorough description of how to extract data from any source, clean it up, shape it as per your requirement using Python and 3rd party APIs. Next you will be familiarised with the process of storing the scrapped data in databases as well as search engines and performing real time analytics on them with Spark Streaming. By the end of this book, you will perfect the art of scraping data for your applications with ease.

This book is now available on [Amazon](http://amzn.to/1PeQ5O0) and [Packt](https://www.packtpub.com/big-data-and-business-intelligence/learning-scrapy).

## What you will learn

- Understand HTML pages and write XPath to extract the data you need
- Write Scrapy spiders with simple Python and do web crawls
- Push your data into any database, search engine or analytics system
- Configure your spider to download files, images and use proxies
- Create efficient pipelines that shape data in precisely the form you want
- Use Twisted Asynchronous API to process hundreds of items concurrently
- Make your crawler super-fast by learning how to tune Scrapy's performance
- Perform large scale distributed crawls with scrapyd and scrapinghub

## Tutorials

* How to Setup Software and Run Examples On A Windows Machine

[![image](https://cloud.githubusercontent.com/assets/789359/24506332/0c016008-1555-11e7-86e3-c736e953a199.PNG)](https://www.youtube.com/watch?v=r84-dsIRFI8)

* Chapter 4 - Create Appery.io mobile application - Updated process

[![image](https://cloud.githubusercontent.com/assets/789359/24486821/e6c99072-1503-11e7-9d45-7eed9c13c7b6.png)](https://www.youtube.com/watch?v=FEbPyQJc3NE)

* Chapter 3 & 9 on a 32-bit VM (for computers limited memory/processing power)

[![image](https://cloud.githubusercontent.com/assets/789359/24482446/26a8eae6-14e9-11e7-9244-d5117954ccea.png)](https://www.youtube.com/watch?v=w9ditoIQ7sU)

## To use Docker directly without installing Vagrant

A `docker-compose.yml` file is included, mainly for those who already have Docker installed. For completeness, here are the links to go about installing Docker.

* For OS X El Capitan 10.11 and later, get [Docker for Mac](https://docs.docker.com/docker-for-mac/).
* For earlier OS X, get [Docker Toolbox for Mac](https://docs.docker.com/toolbox/toolbox_install_mac/).
* For Windows 10 Pro, with Enterprise and Education (1511 November update, Build 10586 or later), get [Docker for Windows](https://docs.docker.com/docker-for-windows/).
* For Windows 7, 8.1 or other 10, get [Docker Toolbox for Windows](https://docs.docker.com/toolbox/toolbox_install_windows/).
* For Ubuntu and other Linux distributions, install
[docker](https://docs.docker.com/engine/installation/linux/ubuntu/) and
[docker-compose](https://docs.docker.com/compose/install/).
  To [avoid having to use sudo when you use the docker command](https://docs.docker.com/engine/installation/linux/linux-postinstall/),
create a Unix group called docker and add users to it:
  1. `sudo groupadd docker`
  2. `sudo usermod -aG docker $USER`

Once you have Docker installed and started, change to the project directory and run:

  1. `docker-compose pull` - To check for updated images
  2. `docker-compose up` - Will scroll log messages as various containers (virtual machines) start up. To stop the containers, Ctrl-C in this window, or enter `docker-compose down` in another shell window.

`docker system prune` will delete the system-wide Docker images, containers, and volumes that are not in use when you want to recover space.

See also [the official website](http://scrapybook.com)
