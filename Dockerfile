# cdeep3m
# there are different versions depending on the cuda version of the system, uncomment the correct one

# cuda 9
#FROM ncmir/cdeep3m AS nc

# cuda 10
#FROM giterdone.crbs.ucsd.edu:8443/ncmir/dev-cdeep3m-docker-c10:latest AS nc

# cuda 11
FROM giterdone.crbs.ucsd.edu:8443/ncmir/dev-cdeep3m-docker-c11:latest as nc



# python3.7 dependencies
RUN apt update
RUN apt install libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6 libgdm-dev libdb4o-cil-dev libpcap-dev libffi-dev libbz2-dev \
-y

# install python3.7
WORKDIR /python
COPY install/Python-3.7.9.tgz /python/Python-3.7.9.tgz
RUN tar xvfz Python-3.7.9.tgz
RUN find /python -type d | xargs chmod 0755
WORKDIR /python/Python-3.7.9
RUN ./configure --prefix=/python
RUN make && make install
ENV PATH=$PATH:/python/bin

# install imod
WORKDIR /imodinstall
COPY install/imod_4.9.12_RHEL7-64_CUDA8.0.sh* /imodinstall/
RUN ls
RUN cat imod_4.9.12_RHEL7-64_CUDA8.0.sh* > imod_4.9.12_RHEL7-64_CUDA8.0.sh
RUN rm imod_4.9.12_RHEL7-64_CUDA8.0.sh?
RUN chmod +x imod_4.9.12_RHEL7-64_CUDA8.0.sh
RUN ./imod_4.9.12_RHEL7-64_CUDA8.0.sh -debian -y
ENV IMOD_DIR=/usr/local/IMOD
ENV PATH=$PATH:/usr/local/IMOD/bin

# rbdb pipeline
WORKDIR /pipeline
COPY pipeline/requirements.txt /pipeline/requirements.txt

# rbdb python dependencies
RUN /python/bin/pip3 install --upgrade pip
RUN /python/bin/pip3 install -r /pipeline/requirements.txt

# more dependencies
RUN apt update
RUN apt install ffmpeg libsm6 libxext6 libjpeg62 -y

# move files
COPY pipeline /pipeline
COPY pipeline_ebib /pipeline_ebib
COPY timing /timing

# set up starting point in docker
WORKDIR /chlamydia_inf
COPY docker_run.bash /chlamydia_inf
COPY run_rbdb.bash /chlamydia_inf
COPY run_ebib.bash /chlamydia_inf
RUN chmod +x run_rbdb.bash
RUN chmod +x run_ebib.bash
RUN chmod +x docker_run.bash

ENTRYPOINT ["/chlamydia_inf/docker_run.bash"]
