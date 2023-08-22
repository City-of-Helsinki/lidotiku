FROM python:3.11-slim-bookworm

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && apt-get -y install --no-install-recommends libgdal32

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER nobody:0

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
