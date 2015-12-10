ENV['VAGRANT_DEFAULT_PROVIDER'] = "docker"

Vagrant.configure("2") do |config|

	# -------------- Web server --------------

	config.vm.define "web" do |web|
	
		web.vm.provider "docker" do |d|
			#d.image = "scrapybook/web"
			d.build_dir = "../scrapybook-docker-web"
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
			#d.image = "scrapybook/spark"
			d.build_dir = "../scrapybook-docker-spark"
			d.name = "spark"
			d.has_ssh = true

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

	# -------------- 3 Scrapyd servers --------------

	{
		"scrapyd1" => 6801,
		"scrapyd2" => 6802, 
		"scrapyd3" => 6803,
	}.each do |host, port|
	
		config.vm.define host do |scp|

			scp.vm.provider "docker" do |d|
				#d.image = "scrapybook/dev"
				d.build_dir = "../scrapybook-docker-dev/trusty/latest"
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
			#d.image = "scrapybook/dev"
			d.build_dir = "../scrapybook-docker-dev/trusty/latest"
			d.name = "dev"
			d.has_ssh = true

			d.link("web:web")
			d.link("spark:spark")
			d.link("scrapyd1:scrapyd1")
			d.link("scrapyd2:scrapyd2")
			d.link("scrapyd3:scrapyd3")

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
end
