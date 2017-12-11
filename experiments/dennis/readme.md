# DeNniS - the MONROE DNS testing tool

This tool serves two purposes.

First, it's an example implementation on how to setup
custom DNS configurations in containers.

Second, it will do DNS name resolutions over all available interfaces,
against all discovered DNS addresses, for the configured hostnames.

This can be used to determine DNS reachability and if DNS queries
are adapted in operator networks, a common practice for content
delivery networks where caches are hosted close to the customer.

