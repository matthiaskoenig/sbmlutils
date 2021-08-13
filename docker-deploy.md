- login to server
- 

## Initial setup
cd /var/git
git clone https://github.com/matthiaskoenig/sbmlutils.git
git checkout sbml4humans
docker-compose -f docker-compose-production.yml up --detach

## Activate page
cp <repo>/nginx/sbml4humans.de /etc/nginx/sites-available/sbml4humans.de
sudo ln -s /etc/nginx/sites-available/sbml4humans.de /etc/nginx/sites-enabled/


## Certificates
### Initial certificates
sudo service nginx stop
sudo certbot certonly
sudo service nginx start
sudo service nginx status


### Certificate renewal
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo certbot certonly --webroot
