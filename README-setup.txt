useradd -G sudo,www-data -m -s /bin/bash build
passwd build
apt-get install vim ccache devscripts quilt dpkg-dev
