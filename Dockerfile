# write a docker file to run the python script
FROM python:3.11.2
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "portfolio_balancer.py"]