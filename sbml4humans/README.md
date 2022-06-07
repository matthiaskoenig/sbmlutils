# SBML4Humans
This document describes the techology and how to setup the SBML4Humans report
for development.

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

## Project setup for development

### Start backend API
Create Python virtual environment and install sbml4humans
``` 
mkvirtualenv sbmlutils
pip install -e .[development]
``` 

Start the API from `src/sbmlutils/report/api.py` either from the python module or via
the command line via 
```bash
python src/sbmlutils/report/api.py
```
This will run the API on port 1444, see for example
http://localhost:1444/api/examples


### Start frontend
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
