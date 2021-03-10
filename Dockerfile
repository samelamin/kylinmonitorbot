FROM python:3.8-slim-buster as production

# dont forget to map source to /app volume

#RUN apt-get -y update
#RUN apt-get -y install pkg-config libsecp256k1-dev

#docker stop kylin-node;docker rm kylin-node;docker run --name kylin-node -id -t kylin-node
#python main.py config/config.yaml
WORKDIR /app
ADD ./app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py", "/config/config.yaml" ]