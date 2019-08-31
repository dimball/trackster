FROM ampervue/ffmpeg

# https://github.com/ampervue/docker-ffmpeg

MAINTAINER David Karchmer <dkarchmer@gmail.com>

# ============================================================================
# As an example, the python script uses FFMPEG to download a movie from the web
# and create a 100x100 thumbnail
#
# ~~~~
# git clone https://github.com/ampervue/docker-ffmpeg
# cd example
# docker build -t thumbnail .
# docker run --rm -ti thumbnail --file http://techslides.com/demos/sample-videos/small.mp4
#
# # Mount current directory on container so that file can be written back to host
# docker run --rm -ti -v ${PWD}:/code thumbnail --file http://techslides.com/demos/sample-videos/small.mp4
# ls thumbnail.jpg
# open thumbnail.jpg
#
# # To run with bash
# docker run --entrypoint bash -ti thumbnail
# ~~~~
# ============================================================================
RUN echo deb http://archive.ubuntu.com/ubuntu trusty universe multiverse >> /etc/apt/sources.list; \
apt-get update -qq && apt-get install -y --force-yes libsqlite3-dev

RUN set -x \
	&& mkdir -p /usr/src/python \
	&& curl -SL "https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz" -o python.tar.xz \
	&& curl -SL "https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz.asc" -o python.tar.xz.asc \
	&& gpg --verify python.tar.xz.asc \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz* \
	&& cd /usr/src/python \
	&& ./configure --enable-shared \
                       --enable-loadable-sqlite-extensions \
	&& make -j$(nproc) \
	&& make install \
	&& ldconfig \
	&& find /usr/local \
		\( -type d -a -name test -o -name tests \) \
		-o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
		-exec rm -rf '{}' + \
	&& rm -rf /usr/src/python

# make some useful symlinks that are expected to exist
#RUN cd /usr/local/bin \
#	&& ln -s easy_install-3.4 easy_install \
#	&& ln -s idle3 idle \
#	&& ln -s pip3 pip \
#	&& ln -s pydoc3 pydoc \
#	&& ln -s python3 python \
#	&& ln -s python-config3 python-config
   
RUN pip3 install --no-cache-dir --upgrade --ignore-installed pip==$PYTHON_PIP_VERSION
WORKDIR /usr/local/src

RUN curl -Os https://www.tortall.net/projects/yasm/releases/yasm-${YASM_VERSION}.tar.gz \
    && tar xzvf yasm-${YASM_VERSION}.tar.gz
                  

# Build YASM
# =================================
WORKDIR /usr/local/src/yasm-${YASM_VERSION}
RUN ./configure \
    && make -j ${NUM_CORES} \
    && make install
# =================================

# Remove all tmpfile and cleanup
# =================================
WORKDIR /usr/local/
RUN rm -rf /usr/local/src
RUN apt-get autoremove -y; apt-get clean -y

# Step 1: Install any Python packages
# ----------------------------------------
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip3 install --upgrade pip
RUN pip3 uninstall youtube_dl
RUN pip3 install --upgrade youtube_dl

RUN pip3 install -r requirements.txt

# Step 2: Copy Python script
# ----------------------------------------

ADD app /code/app

# Step 3: Configure entrypoint
# ----------------------------------------

CMD           ["-h"]
ENTRYPOINT    ["python", "app/sbin/server.py"]
