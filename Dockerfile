FROM helsinki.azurecr.io/ubi9/python-312-gdal

RUN dnf update -y

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER nobody:0

EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
