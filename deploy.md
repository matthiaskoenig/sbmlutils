# Deployment `sbml4humans`
This document provides instructions to deploy `sbml4humans` on a server. In many configurations a proxy server is used which proxies the requests to the services running in docker containers. The setup consists normally of setting up the proxy server (with https certificates) and the server with running the docker containers.
## Setup proxy
- login to proxy server `denbi-head`

**Activate page**  
The page must be copied and activated. Make sure to **update the IP** of the server in nginx configuration!
```
cp <repo>/nginx/sbml4humans.de /etc/nginx/sites-available/sbml4humans.de
sudo ln -s /etc/nginx/sites-available/sbml4humans.de /etc/nginx/sites-enabled/
```

### Certificates
#### Initial certificates
```
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo service nginx stop
sudo certbot certonly

-> sbml4humans.de www.sbml4humans.de

sudo service nginx start
sudo service nginx status
```

#### Certificate renewal
```
sudo certbot certonly --webroot -w /usr/share/nginx/letsencrypt -d sbml4humans.de -d www.sbml4humans.de --dry-run
```

## Setup server
On the actual server the containers are orchestrated using `docker-compose`.
Login to server `denbi-node-2`.

### Initial setup
```
cd /var/git
git clone https://github.com/matthiaskoenig/sbmlutils.git
```

**start containers**
Pull latest changes 
```
./deploy.sh
```
