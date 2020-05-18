# Overview

OpenStack is a reliable cloud infrastructure. Its mission is to produce
the ubiquitous cloud computing platform that will meet the needs of public
and private cloud providers regardless of size, by being simple to implement
and massively scalable.

OpenStack Compute, codenamed Nova, is a cloud computing fabric controller. In
addition to its "native" API (the OpenStack API), it also supports the Amazon
EC2 API.

This charm provides the cloud controller service for the OpenStack Nova cell
and includes the nova-conductor service.

OpenStack Rocky or later is required for the Nova cells feature.

Please refer to the [Additional Nova Cells][cdg-app-nova-cells] appendix in the
[OpenStack Charms Deployment Guide][cdg] for details.

# Bugs

Please report bugs on [Launchpad][lp-nova-cells].

For general questions please refer to the OpenStack [Charm Guide][cg].

<!-- LINKS -->

[cg]: https://docs.openstack.org/charm-guide/latest/
[cdg-app-nova-cells]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/app-nova-cells.html
[cdg]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/index.html
[lp-nova-cells]: https://bugs.launchpad.net/charm-nova-cell-controller/+filebug
