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
sudo service nginx stop
sudo certbot certonly
sudo service nginx start
sudo service nginx status
```


#### Certificate renewal
```
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo certbot certonly --webroot
```

## Setup server
On the actual server the containers are orchestrated using `docker-compose`.
Login to server `denbi-node2`.

### Initial setup
```
cd /var/git
git clone https://github.com/matthiaskoenig/sbmlutils.git
git checkout sbml4humans
```

**start containers**
```
docker-compose -f docker-compose-production.yml up --force-recreate --build --detach
```

### Update
Pull latest changes 
```
docker-compose -f docker-compose-production.yml up --force-recreate --build --detach
```




