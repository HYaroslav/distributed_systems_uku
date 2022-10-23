# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app

#
#ENTRYPOINT [ "python" ]

EXPOSE 80

# 
#CMD ["python", "-m", "flask", "--app", "app/master.py", "run", "--host", "0.0.0.0", "--port", "8080"]
CMD ["python", "app/secondary.py"]
