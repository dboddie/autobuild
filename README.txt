Setting up the build machine
----------------------------

The build machine is typically configured to have a build user, created by
the root user with the following commands:

  useradd -G sudo,www-data -m -s /bin/bash build
  passwd build

It's useful to install some tools for maintenance:

  apt-get install vim ccache devscripts quilt dpkg-dev

It's also a good idea to create a file containing authorised keys so that
you can log in securely without needing a password. Make sure that the
build user has an .ssh directory:

  mkdir ~build/.ssh

Export your public key on your local machine using

  gpg -a --export <key-ID> > pub.key

Copy it to the build machine and append it to the build user's authorised
keys file:

  cat pub.key >> ~build/.ssh/authorized_keys


Configuring the build system
----------------------------

On the build machine, the /etc/sudoers file should include the following line:

build   ALL=(ALL:ALL) NOPASSWD: /usr/bin/autobuild-builder.py, /usr/sbin/pbuilder, /usr/bin/pdebuild

On some systems, pbuilder is in the /usr/bin directory.

The autobuild and python-apt-repo packages need to be installed.

If you want to reuse packages that have been built and published to a repository
created by the python-apt-repo-setup.py tool, you need to import the signing key
you intend to use into the trusted keyring before creating chroots.

Create a key using gpg:

  gpg --gen-key

Export it to a file, using the appropriate <key-ID>:

  gpg -a --export <key-ID> > sign.key

Add it to the apt keyring:

  apt-key add sign.key

Set up chroots using the autobuild-builder.py tool. For example:

  autobuild-builder.py create precise-amd64 templates/metno /home/build/chroots precise

The repositories to manage need to be checkout out and registered with the
autobuild-repo.py tool. For example:

  autobuild-repo.py add diana /home/build/local/src/diana-trunk

The python-apt-repo-setup.py tool needs to be run:

  python-apt-repo-setup.py create /home/build/public_html/repo precise contrib

The .autobuild-apt-repo file needs to be created in the build user's home directory
using the following command:

  python -c "open('.autobuild-apt-repo', 'w').write('precise-amd64: /home/build/public_html/repo\tprecise\tcontrib\thttp://localhost/~build/repo')

Copy apt repository signing keys to the build user's home directory and import
them using the following command:

  gpg --import sign*.key

Run the daemon using the following commands:

  export ADDR=`python -c "import os; print os.popen('/sbin/ifconfig').readlines()[1].strip().split()[1][5:]"`
  autobuild-daemon.py $ADDR:8080

