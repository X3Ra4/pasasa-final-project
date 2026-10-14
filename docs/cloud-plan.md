# Cloud Solutions adaptation

Goal: adapt PASASA for the AWS course in the cloud-solutions-aws branch without changing main.

Design: one Ubuntu 24.04 EC2 instance, PostgreSQL on localhost, Django served by Gunicorn behind Nginx. A dedicated systemd service loads /etc/pasasa/.env through EnvironmentFile, restarts on failure and starts at boot. Code is cloned/pulled from this GitHub branch. Uploaded media lives outside the checkout.

The user authorized the branch adaptation and upload. Real EC2 access has been requested; no cloud resources will be provisioned or claimed as deployed without access.

- [x] Add failing cloud configuration and health-check tests.
- [x] Implement PostgreSQL/cloud settings and database health endpoint.
- [x] Add pinned Linux dependencies, systemd/Nginx configs, bootstrap/update scripts and environment example.
- [x] Test Django with PostgreSQL and Gunicorn on Linux; validate shell, systemd and Nginx configuration.
- [x] Write Ukrainian topic, architecture, EC2 setup and evidence instructions.
- [x] Independent review, fixes, final checks; publish only cloud-solutions-aws.

Review focus: missing secrets must fail startup; HTTP/HTTPS must behave as documented; migrations and uploaded media survive code updates; PostgreSQL/Gunicorn never bind publicly; scripts must not overwrite an existing unrelated deployment.

Independent review found no critical/important blockers. Incorporated its deployment-order improvement: stop Gunicorn before changing the checkout or dependencies, accepting maintenance downtime to avoid mixed-version requests. Real AWS/systemd boot/TLS verification remains explicitly pending EC2 access.

Published cloud-solutions-aws to origin and verified its remote commit. Main remains at 40b13679b2455aee83e998f00bf2dc99d314f6bc. Validation: 23 tests on SQLite and PostgreSQL, successful Linux/Gunicorn/Nginx checks; see CLOUD_VERIFICATION.md.
