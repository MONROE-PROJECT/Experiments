
# Tunnelbox-server
1. Scheduler uses pyotp to generate an OTP token that is future-valid at container start time
2. The container calls a simple rest api on the tunnelbox, submits the OTP and the container-generated public key
3. The tunnelbox validates the OTP && stores the public key into a authorized_keys.d directory (which purges files older than X hours)
4. and the container can now establish the tunnel connection.


The container requires that docker is installed and working.
