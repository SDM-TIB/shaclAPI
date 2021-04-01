FROM python:3.8

WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD [ "./wait-for-it.sh","0.0.0.0:14000", "--", "python", "run.py"]