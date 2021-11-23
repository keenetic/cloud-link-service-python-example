# Keenetic Link Daemon

## Setup Instructions

Download actual NDSS SSL certificate from [http://pki.ndm9.xyz/4096-NDM-root-ca.crt]

Flask is starting by default on 127.0.0.1, have to change to 0.0.0.0 in app.run()
Request to ndmp/linkDaemon w/o params throws 500 error, instead of 400
Hardcoded path - /tmp/link-daemon-demo
Remove trailing slash in NDSS_SERVER URL

## NDSS config

### data/settings/ndss/ndmp-services.json

Add service_id params

### data/settings/ndss/ndmp-domains.json

Add linkdaemon endpoint URL

### data/settings/ndss/ndrs-cookies.json

Add ndmpOwnerId cookie for licenses

>ndmp component is required on CPE

## API Error codes

- **0x100** -- NDSS Exception
- **0x101** -- Unexpected answer from NDSS
- **0x122** -- Linking was declined by NDSS

- **0x200** -- Missing some mandatory parameters
- **0x201** -- Service tag (license) is not valid

- **0x300** -- Missing keys in local key storage. Need to link device.
- **0x301** -- Failed to load keys (record exists, but missing some data)
- **0x302** -- Key is in incorrect format

- **0x401** -- API Authorization failed
- **0x414** -- Signature verification failed. See Error Details for more information

## Proxied errors from CPE device

- **0x0300** -- No acknowledge after info request. (30 sec)
- **0x0400** -- Unable to get from or to send information to device. Is device off?
- **0x0143** -- Authorization was declined by Keenetic Device. Is device linked with provider?
