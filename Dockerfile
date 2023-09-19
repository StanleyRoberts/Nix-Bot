FROM python:3.10.8-bullseye
WORKDIR /Nix
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN python -m playwright install
COPY . .
CMD ["python3", "-u", "-O", "src/Nix.py"]
