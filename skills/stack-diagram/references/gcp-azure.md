# Google Cloud and Azure diagrams

Read this when the stack runs on Google Cloud or Azure. Each vendor has its own icons, naming and group rules. The vendors' own diagram styles are not copied: icons go on the normal white tile, and edges and the legend stay as in the template.

## Vendor rule

A vendor's rules, including [AWS's](aws.md), apply only inside that vendor's group. A user beside the group, or an edge that crosses into it, keeps the normal tiles, groups, edges and legend.

## Icons

Fetch with `name:gcp/<Product>` or `name:azure/<Name>`. Both read the vendor's official package at run time, keep it in memory and need `--allow-network`. The hosts are `services.google.com` for Google Cloud, `learn.microsoft.com` and `arch-center.azureedge.net` for Azure. Offline, the node gets a pictogram.

```bash
python3 scripts/fetch_icons.py <job>/icons --allow-network "gcp:google-cloud" "run:gcp/cloud-run" "lb:gcp/load-balancing"
python3 scripts/fetch_icons.py <job>/icons --allow-network "azure:azure/Azure-A" "app:azure/app-service" "vnet:azure/vnet"
```

- A miss prints every name. The `gcp-*`, `google-cloud-*` and `azure-*` slugs use the same packages, and what a package lacks falls back to a pictogram, never a third-party copy.
- Always write the prefix for a service. A bare `bigquery` or `cosmos` goes through the third-party chain.
- `gcp` and `google-cloud` alone are the Google Cloud mark, for the group label. `azure` alone is the Azure mark from the Azure package.
- **Google Cloud:** only core products have their own icon. Every other product shares its category's icon, so Cloud Load Balancing and Cloud CDN both get Networking. The `Cloud` and `Google` prefixes are optional, and some short forms work (`vpc`, `iam`, `kms`, `iap`, `gce`, `gcs`). `gcp/storage` is the Storage category; Cloud Storage is `gcp/cloud-storage`. Gemini and Firebase are not in the packages.
- **Azure:** the `Azure-` and `Microsoft-` prefixes and a plural `s` are optional, and short forms such as `aks`, `vm`, `vnet`, `nsg`, `waf`, `blob`, `cosmos`, `redis`, `postgres`, `functions`, `apim` work. Microsoft Entra ID has a separate icon set: pass its official file as `name=URL`.
- Never crop, flip, rotate or reshape a vendor icon, and use it only for the service it stands for. Microsoft allows its icons in architecture diagrams, training material and documentation only. Redistribution of either package is unconfirmed, so keep packages and loose icon files out of every repository.
- **Credit:** `build.py` credits source `gcp` as `Google Cloud icons` and `azure` as `Azure icons`.

## Drawing rules

- **Tiles:** the normal white `tile`, not `bare`. Edges stay `e`, `n` and `n dash`, with the legend.
- **Names:** the product's full name beside its icon (`Cloud Load Balancing`, `Azure SQL Database`), never `LB` or `SQL`. Shared icons make the name the only difference. Widen a node whose name would wrap (`left:<centerX-76>px; width:152px`).
- **Google Cloud groups:** `group gcp` with `gcp:google-cloud` in the label, plus `vpc`, `region`, `subnet` or `zone`. A VPC is global and a subnet is regional, so put the region inside the VPC, never the VPC inside a region. Global and serverless services (an external load balancer, Cloud Storage, Cloud Run) stay outside the VPC.
- **Azure groups:** `group azure` with `azure:azure/Azure-A` in the label, plus `rg`, `region`, `vnet`, `subnet` or `zone`. A `vnet` or `subnet` label may carry its icon (`vnet:azure/vnet`, `subnet:azure/subnet`). A VNet belongs to one region, so it goes inside the region. Global services such as Front Door stay outside the region. App Service sits outside the VNet unless it runs in an App Service Environment. A PaaS service reached through a private endpoint can sit inside the VNet with `private endpoint` as its role.
