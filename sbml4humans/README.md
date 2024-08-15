# SBML4Humans
This document describes the technology and how to setup the development 
environment for the SBML4Humans report.

## Project setup for development

### Start backend API and frontend (docker compose)
The simplest setup is to start the frontend and backend via the docker-compose scripts.

```
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

Alternatively the backend and frontend can be run directly on the machine. This most likely requires updates of the local `node` and `npm` packages.


### Start backend API (local)
Create Python virtual environment and install sbml4humans
```bash
mkvirtualenv sbml4humans --python=python3.12
pip install -e .[sbml4humans,development] --upgrade
``` 

Start the backend API from `src/sbmlutils/report/api.py` either from the python module or via
the command line via 
```bash
python src/sbmlutils/report/api.py
```
This will run the API on port 1444. Check that the API is running using a browser
http://localhost:1444/api/examples


### Start frontend (local)
**Install all dependencies**  
```
cd sbml4humans
npm install
```

**Compiles and hot-reloads for development**
```
npm run serve
```
This starts the frontend server on http://localhost:3456/ which communicates with 
the running backend API.


## Technology
1. Backend API: ```sbmlutils``` Python package served using FastAPI service [https://fastapi.tiangolo.com/]
2. Frontend User Interface: Build using Vue.js 3 [https://vuejs.org/]
    - TypeScript + SCSS
    - Vuex
    - Vue Router
3. Frontend UI/UX Package: Ant Design Vue [https://www.antdv.com/docs/vue/introduce/]

## Vue.js devtools
Vue 3 is only working with the beta version of the devtools available from
https://github.com/vuejs/vue-devtools/releases
To install the devtools use the `xpi` file from the download and install in Firefox.
