- login to server
- 

## Initial setup



## Activate page
cp <repo>/nginx/sbml4humans.de /etc/nginx/sites-available/sbml4humans.de
sudo ln -s /etc/nginx/sites-available/sbml4humans.de /etc/nginx/sites-enabled/


## Certificates
### Certificate renewal
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo certbot certonly --webroot
