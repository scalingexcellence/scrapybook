ENV['VAGRANT_DEFAULT_PROVIDER'] = "docker"

Vagrant.configure("2") do |config|

	# -------------- Web server --------------

	config.vm.define "web" do |web|
	
		web.vm.provider "docker" do |d|
			d.image = "scrapybook/web"
			#d.build_dir = "../scrapybook-docker-web"
			d.name = "web"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
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
			#d.has_ssh = true

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
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
			d.image = "elasticsearch"
			d.name = "es"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
		end
		
		es.vm.synced_folder ".", "/vagrant", disabled: true
		
		es.vm.network "forwarded_port", guest: 9200, host: 9200
		es.vm.hostname = "es"
	end
	

	# -------------- Redis server --------------

	config.vm.define "redis" do |redis|
	
		redis.vm.provider "docker" do |d|
			d.image = "redis"
			d.name = "redis"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
		end
		
		redis.vm.synced_folder ".", "/vagrant", disabled: true
		
		redis.vm.network "forwarded_port", guest: 6379, host: 6379
		redis.vm.hostname = "redis"
	end
	

	# -------------- MySQL server --------------

	config.vm.define "mysql" do |mysql|
	
		mysql.vm.provider "docker" do |d|
			d.image = "mysql:latest"
			d.create_args = ["-e" ,"MYSQL_ROOT_PASSWORD=pass"]
			d.name = "mysql"

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
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
				#d.build_dir = "../scrapybook-docker-dev/trusty/latest"
				d.name = host

				d.vagrant_machine = "docker-provider"
				d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
				d.force_host_vm = true
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
			#d.build_dir = "../scrapybook-docker-dev/trusty/latest"
			d.name = "dev"
			#d.has_ssh = true

			d.link("web:web")
			d.link("spark:spark")
			d.link("scrapyd1:scrapyd1")
			d.link("scrapyd2:scrapyd2")
			d.link("scrapyd3:scrapyd3")
			d.link("mysql:mysql")
			d.link("redis:redis")
			d.link("es:es")

			d.vagrant_machine = "docker-provider"
			d.vagrant_vagrantfile = "./Vagrantfile.dockerhost"
			d.force_host_vm = true
		end
		
		dev.vm.synced_folder ".", "/root/book"
		
		dev.vm.network "forwarded_port", guest: 6800, host: 6800
		dev.vm.hostname = "dev"
	end

	config.ssh.username = 'root'
	config.ssh.private_key_path = 'insecure_key'
	
	# -------------- Bare VM - normaly disabled --------------
	
	config.vm.define "plain", autostart: false do |plain|
		plain.ssh.username = nil
		plain.ssh.private_key_path = nil
	
		# A plain ubuntu with gui
		plain.vm.box = "ubuntu/trusty64"
		
		config.vm.provision "shell", inline: <<-SHELL
			apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
			echo 'deb https://apt.dockerproject.org/repo ubuntu-trusty main' | tee --append /etc/apt/sources.list.d/docker.list > /dev/null
			apt-get update
			apt-get install -y git docker-engine
			usermod -aG docker vagrant
			
			wget https://releases.hashicorp.com/vagrant/1.7.4/vagrant_1.7.4_x86_64.deb
			dpkg -i vagrant_1.7.4_x86_64.deb
			rm vagrant_1.7.4_x86_64.deb
		SHELL

		# Set the mem/cpu requirements
		plain.vm.provider :virtualbox do |vb|
			vb.memory = 2048
			vb.cpus = 2
			vb.name = "plain"
			vb.check_guest_additions = false
		end
	end
end
