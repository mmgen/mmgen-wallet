#!/bin/sh
#
# msys2-sshd-setup.sh — configure sshd on MSYS2 and run it as a Windows service
#
# Replaces ssh-host-config <https://github.com/openssh/openssh-portable/blob/master/contrib/cygwin/ssh-host-config>
# Adapted from <https://ghc.haskell.org/trac/ghc/wiki/Building/Windows/SSHD> by Sam Hocevar <sam@hocevar.net>
# Adapted from <https://gist.github.com/samhocevar/00eec26d9e9988d080ac> by David Macek
#
# Prerequisites:
#   - pacman -S openssh cygrunsrv
#
#
# Adapted by the MMGen Project from https://www.msys2.org/wiki/Setting-up-SSHd/
#
# MMGen notes:
#    Open PowerShell (Run as Administrator)
#    system32> net user administrator /active:yes
#    system32> C:\\msys64\usr\bin\bash.exe --login
#    $ path/to/msys2-sshd-setup.sh
#
#    Now the SSH service should start automatically when Windows is rebooted.
#    You can manually start and stop the service by running:
#        net start msys2_sshd
#        net stop msys2_sshd

set -e

# Configuration
UNPRIV_USER=sshd # DO NOT CHANGE; this username is hardcoded in the openssh code
UNPRIV_NAME="Privilege separation user for sshd"
EMPTY_DIR=/var/empty

# Check installation sanity
if ! cygrunsrv -v >/dev/null; then
    echo "ERROR: Missing 'cygrunsrv'. Try: pacman -S cygrunsrv."
    exit 1
fi

if ! ssh-keygen -A; then
    echo "ERROR: Missing 'ssh-keygen'. Try: pacman -S openssh."
    exit 1
fi

# The unprivileged sshd user (for privilege separation)
add="$(if ! net user "${UNPRIV_USER}" >/dev/null; then echo "//add"; fi)"
if ! net user "${UNPRIV_USER}" ${add} //fullname:"${UNPRIV_NAME}" \
              //homedir:"$(cygpath -w ${EMPTY_DIR})" //active:no; then
    echo "ERROR: Unable to create Windows user ${UNPRIV_USER}"
    exit 1
fi

# Add or update /etc/passwd entries
if test -f /etc/passwd; then
    sed -i -e '/^'"${UNPRIV_USER}"':/d' /etc/passwd
    SED='/^'"${UNPRIV_USER}"':/s?^\(\([^:]*:\)\{5\}\).*?\1'"${EMPTY_DIR}"':/bin/false?p'
    mkpasswd -l -u "${UNPRIV_USER}" | sed -e 's/^[^:]*+//' | sed -ne "${SED}" >> /etc/passwd
    mkgroup.exe -l > /etc/group
fi

# Finally, register service with cygrunsrv and start it
cygrunsrv -R msys2_sshd || true
sleep 1
cygrunsrv -I msys2_sshd -d "MSYS2 sshd" -p /usr/bin/sshd.exe -a "-D -e" -y tcpip
