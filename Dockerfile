
FROM ncmir/cdeep3m AS nc

RUN apt update
RUN apt install libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6 libgdm-dev libdb4o-cil-dev libpcap-dev libffi-dev libbz2-dev \
-y

WORKDIR /python
RUN wget https://www.python.org/ftp/python/3.7.9/Python-3.7.9.tgz
RUN tar xvfz Python-3.7.9.tgz
RUN find /python -type d | xargs chmod 0755
WORKDIR /python/Python-3.7.9
RUN ./configure --prefix=/python
RUN make && make install
ENV PATH=$PATH:/python/bin

WORKDIR /pipeline
COPY requirements.txt /pipeline/requirements.txt

#RUN python3 -m venv $VIRTUAL_ENV

#RUN . bin/activate

RUN /python/bin/pip3 install --upgrade pip
RUN /python/bin/pip3 install -r /pipeline/requirements.txt

RUN apt update ##[edited]
RUN apt install ffmpeg libsm6 libxext6 -y

COPY . /pipeline


#FROM ncmir/cdeep3m AS nc
#COPY --from=pyvenv /pipeline /pipeline
#COPY --from=pyvenv /usr/local/lib /usr/local/lib
#COPY --from=pyvenv /lib/x86_64-linux-gnu/libc.so.6 /lib/x86_64-linux-gnu/libc.so.6
#COPY . /pipeline

#WORKDIR /pipeline

#RUN mkdir /images
#RUN mkdir /images/nrml
#RUN mkdir /images/edt
