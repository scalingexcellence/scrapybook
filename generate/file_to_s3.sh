#!/bin/sh

s3cmd put --acl-public --guess-mime-type $2 s3://$1/$2

