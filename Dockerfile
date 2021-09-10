FROM python:3.8.11-slim-buster

# install dependencies
COPY requirements.txt /travshaclAPI/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==21.1.* setuptools==57.0.0 gunicorn==20.1.* && \
    python -m pip install --no-cache-dir -r /travshaclAPI/requirements.txt

# copy the source code into the container
COPY . /travshaclAPI
RUN cd /travshaclAPI && python3 setup.py install
WORKDIR /travshaclAPI

# start the Flask app
ENTRYPOINT ["gunicorn", "-c", "/travshaclAPI/gunicorn.conf.py", "run:app"]
