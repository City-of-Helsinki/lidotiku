FROM container-registry.platta-net.hel.fi/devops/python:3.11-slim-bookworm

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && apt-get -y install --no-install-recommends gdal-bin

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER nobody:0

EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
