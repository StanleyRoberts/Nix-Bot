FROM python:3.10.8-bullseye
WORKDIR /Nix
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "-u", "-O", "src/Nix.py"]
