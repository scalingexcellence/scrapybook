Vagrant.configure("2") do |config|

	config.vm.define "web" do |web|
		web.vm.provider "docker" do |d|
			#d.image = "scrapybook/web"
                        d.build_dir = "../scrapybook-docker-web"
			d.name = "web"
		end
		web.vm.network "forwarded_port", guest: 9312, host: 9312
                web.vm.synced_folder ".", "/vagrant", disabled: true
	end

        config.vm.define "spark" do |spark|
            spark.vm.provider "docker" do |d|
                #d.image = "scrapybook/spark"
                d.build_dir = "../scrapybook-docker-spark"
                d.name = "spark"
                d.has_ssh = true
            end
            spark.vm.synced_folder ".", "/root/book"
            spark.vm.network "forwarded_port", guest: 21, host: 21
            (30000..30009).each do |port|
                spark.vm.network "forwarded_port", guest: port, host: port
            end
        end
	
	config.vm.define "dev", primary: true do |dev|
		dev.vm.provider "docker" do |d|
			#d.image = "scrapybook/dev"
                        d.build_dir = "../scrapybook-docker-dev/trusty/latest"
			d.name = "dev"
			d.has_ssh = true
			d.link("web:web")
			d.link("spark:spark")
		end
            dev.vm.synced_folder ".", "/root/book"
            dev.vm.network "forwarded_port", guest: 6800, host: 6800
    end

    config.ssh.username = 'root'
    config.ssh.private_key_path = 'insecure_key'
end
