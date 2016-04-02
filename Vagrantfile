ENV['VAGRANT_DEFAULT_PROVIDER'] = "docker"

host_vagrantfile = "./Vagrantfile.dockerhost"

Vagrant.configure("2") do |config|

	# -------------- Web server --------------

	config.vm.define "web" do |web|
	
		web.vm.provider "docker" do |d|
			d.image = "scrapybook/web"
			#d.build_dir = "../scrapybook-docker-web"
			d.name = "web"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		web.vm.synced_folder ".", "/vagrant", disabled: true
		
		web.vm.network "forwarded_port", guest: 9312, host: 9312
		web.vm.hostname = "web"
	end

	# -------------- Spark server --------------

	config.vm.define "spark" do |spark|
	
		spark.vm.provider "docker" do |d|
			d.image = "scrapybook/spark"
			#d.build_dir = "../scrapybook-docker-spark"
			d.name = "spark"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		spark.vm.synced_folder ".", "/root/book"
		
		spark.vm.network "forwarded_port", guest: 21, host: 21
		(30000..30009).each do |port|
			spark.vm.network "forwarded_port", guest: port, host: port
		end
		spark.vm.hostname = "spark"
	end


	# -------------- ES server --------------

	config.vm.define "es" do |es|
	
		es.vm.provider "docker" do |d|
			d.image = "scrapybook/es"
			#d.build_dir = "../scrapybook-docker-es"
			d.name = "es"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		es.vm.synced_folder ".", "/vagrant", disabled: true
		
		es.vm.network "forwarded_port", guest: 9200, host: 9200
		es.vm.hostname = "es"
	end
	

	# -------------- Redis server --------------

	config.vm.define "redis" do |redis|
	
		redis.vm.provider "docker" do |d|
			d.image = "scrapybook/redis"
			#d.build_dir = "../scrapybook-docker-redis"
			d.name = "redis"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		redis.vm.synced_folder ".", "/vagrant", disabled: true
		
		redis.vm.network "forwarded_port", guest: 6379, host: 6379
		redis.vm.hostname = "redis"
	end
	

	# -------------- MySQL server --------------

	config.vm.define "mysql" do |mysql|
	
		mysql.vm.provider "docker" do |d|
			d.image = "scrapybook/mysql"
			#d.build_dir = "../scrapybook-docker-mysql"
			d.name = "mysql"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		mysql.vm.synced_folder ".", "/vagrant", disabled: true
		
		mysql.vm.network "forwarded_port", guest: 3306, host: 3306
		mysql.vm.hostname = "mysql"
	end
	# -------------- 3 Scrapyd servers --------------

	{
		"scrapyd1" => 6801,
		"scrapyd2" => 6802, 
		"scrapyd3" => 6803,
	}.each do |host, port|
	
		config.vm.define host do |scp|

			scp.vm.provider "docker" do |d|
				d.image = "scrapybook/dev"
				#d.build_dir = "../scrapybook-docker-dev"
				d.name = host
				
				d.link("spark:spark")
				d.link("web:web")

				d.vagrant_machine = "docker-provider"
				d.vagrant_vagrantfile = host_vagrantfile
			end
		
			scp.vm.synced_folder ".", "/vagrant", disabled: true
		
			scp.vm.network "forwarded_port", guest: 6800, host: port
			scp.vm.hostname = host
		end
	end

	# -------------- Dev machine --------------

	config.vm.define "dev", primary: true do |dev|
	
		dev.vm.provider "docker" do |d|
			d.image = "scrapybook/dev"
			#d.build_dir = "../scrapybook-docker-dev"
			d.name = "dev"

			d.link("web:web")
			d.link("spark:spark")
			d.link("scrapyd1:scrapyd1")
			d.link("scrapyd2:scrapyd2")
			d.link("scrapyd3:scrapyd3")
			d.link("mysql:mysql")
			d.link("redis:redis")
			d.link("es:es")

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = host_vagrantfile
		end
		
		dev.vm.synced_folder ".", "/root/book"
		
		dev.vm.network "forwarded_port", guest: 6800, host: 6800
		dev.vm.hostname = "dev"
	end

	config.ssh.username = 'root'
	config.ssh.private_key_path = 'insecure_key'
end
