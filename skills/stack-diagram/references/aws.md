# AWS diagrams

Read this when the stack runs on AWS. AWS diagrams follow AWS's own drawing rules, and people who work with AWS notice when they don't.

## Icons

Fetch each service with `name:aws/<Name>`, for example `lambda:aws/lambda`, `aws:aws/AWS-Cloud-logo`, `s3:aws/s3`. The script reads AWS's official package at run time and keeps it in memory.

- The `AWS-` and `Amazon-` prefixes are optional, and common acronyms work: `s3`, `sqs`, `sns`, `ses`, `ecs`, `eks`, `ecr`, `elb`, `alb`, `nlb`, `iam`, `kms`, `msk`, `vpc`.
- A miss prints every name in the package.
- The slugs `aws`, `amazonwebservices` and `aws-*` use the same package, and what it lacks falls back to a pictogram, so a third-party copy never ships by accident.
- Always write the `aws/` prefix for a service. A bare `dynamodb` goes through the third-party chain.
- AWS allows these icons in diagrams, and redistribution is unconfirmed. Keep the package and loose icon files out of every repository.

## Drawing rules

- **Icons:** service icons carry their own square and work on both grounds, so use `tile bare`. A white tile only doubles the frame.
- **People and generic nodes:** use AWS's general icons (`user:aws/General-User`; also `General-Users`, `General-Client`, `General-Internet`, `General-Server`) in `tile bare res` with the template's `lt`/`dk` pair.
- **Groups:** `group aws` for AWS Cloud, with `aws:aws/AWS-Cloud-logo` in the label. Add `region`, `az`, `vpc`, `private` or `public` for the rest. These get square corners, outline only, an ink label, no vendor tint, and a 30px icon flush in the corner.
- **Subnets:** inside a VPC, show public and private subnets when you know or can safely infer the split: an internet-facing load balancer in public, app servers and databases in private. A flat VPC is the first thing AWS people notice.
- **Edges:** one colour and an open arrowhead: `<path class="aws" ... marker-end="url(#open)"/>`, `aws dash` for dev and deploy, plain `.el` labels, and no legend.
- **Names:** `Amazon S3` and `AWS Fargate`, never a bare `S3`. A short form such as `ALB` goes in the role line under the full name (`Elastic Load Balancing`). Names may take two lines, but `Amazon` or `AWS` must stay on the first word's line. If it would wrap right after the prefix, widen that node (`left:<centerX-76>px; width:152px`).
- **Credit:** `build.py` credits source `aws` as `AWS Architecture Icons`.
