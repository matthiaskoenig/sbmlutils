```
cd docker
docker build --tag pylibsbml --file Dockerfile-pylibsbml --no-cache .
docker build --tag pylibnuml --file Dockerfile-pylibnuml --no-cache .
docker build --tag pylibsedml --file Dockerfile-pylibsedml --no-cache .

cd ..
docker build --tag sbmlutils --no-cache .
docker run --name sbmlutils -it sbmlutils bash

```