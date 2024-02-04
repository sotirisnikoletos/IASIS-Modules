FROM python:2
FROM java:8
ADD get-pip.py .
RUN python get-pip.py
ADD ./requirements.txt .
RUN pip install -r ./requirements.txt
COPY ./medknow/ ./medknow
ADD test.py .
ADD start.sh .
CMD ["./start.sh"]
