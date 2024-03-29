FROM python:3.8.13-slim-bullseye

# install dependencies
COPY requirements.txt /shaclAPI/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==22.2.* gunicorn==20.1.* && \
    python -m pip install --no-cache-dir -r /shaclAPI/requirements.txt

# copy the source code into the container
COPY . /shaclAPI
WORKDIR /shaclAPI

# start the Flask app
ENTRYPOINT ["gunicorn", "-c", "/shaclAPI/gunicorn.conf.py", "run:app"]
