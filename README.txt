On the build machine, the /etc/sudoers file should include the following line:

build   ALL=(ALL:ALL) NOPASSWD: /usr/bin/autobuild-builder.py, /usr/bin/pdebuild

The autobuild and python-apt-repo packages need to be installed.

Some chroots need to be set up using the autobuild-builder.py tool. For example:

  autobuild-builder.py create precise-amd64 templates/metno /home/build/chroots precise

The repositories to manage need to be checkout out and registered with the
autobuild-repo.py tool. For example:

  autobuild-repo.py add diana /home/build/local/src/diana-trunk

The python-apt-repo-setup.py tool needs to be run:

  python-apt-repo-setup.py create /home/build/public_html/repo precise contrib

The .autobuild-apt-repo file needs to be created in the build user's home directory and
given the following contents:

precise-amd64: /home/build/public_html/repo precise contrib

Run the daemon using the following commands:

  export ADDR=`python -c "import os; print os.popen('/sbin/ifconfig').readlines()[1].strip().split()[1][5:]"`
  autobuild-daemon.py $ADDR:8080

