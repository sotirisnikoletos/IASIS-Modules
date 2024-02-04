FROM python:2
RUN pip install --upgrade pip
ADD ./requirements.txt .
RUN pip install -r ./requirements.txt
COPY ./medknow/ ./medknow
ADD test.py .
CMD [ "python", "./test.py" ]
