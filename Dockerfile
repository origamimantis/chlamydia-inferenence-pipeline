# ncmir
FROM ncmir/cdeep3m AS nc

# python3.7 dependencies
RUN apt update
RUN apt install libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6 libgdm-dev libdb4o-cil-dev libpcap-dev libffi-dev libbz2-dev \
-y

# install python3.7
WORKDIR /python
RUN wget https://www.python.org/ftp/python/3.7.9/Python-3.7.9.tgz
RUN tar xvfz Python-3.7.9.tgz
RUN find /python -type d | xargs chmod 0755
WORKDIR /python/Python-3.7.9
RUN ./configure --prefix=/python
RUN make && make install
ENV PATH=$PATH:/python/bin

# rbdb pipeline
WORKDIR /pipeline
COPY pipeline/requirements.txt /pipeline/requirements.txt

# rbdb python dependencies
RUN /python/bin/pip3 install --upgrade pip
RUN /python/bin/pip3 install -r /pipeline/requirements.txt

# more dependencies
RUN apt update
RUN apt install ffmpeg libsm6 libxext6 -y

# move files
COPY pipeline /pipeline
COPY pipeline_ebib /pipeline_ebib
COPY timing /timing

# set up starting point in docker
WORKDIR /chlamydia_inf
COPY docker_run.bash /chlamydia_inf
COPY run_rbdb.bash /chlamydia_inf
COPY run_ebib.bash /chlamydia_inf

ENTRYPOINT ["/chlamydia_inf/docker_run.bash"]
