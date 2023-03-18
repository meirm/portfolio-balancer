#!/bin/bash
set -o errexit
cd /opt/git/riunx/portfolio_balancing
. env/bin/activate
./portfolio_balancer.py --report-transaction
