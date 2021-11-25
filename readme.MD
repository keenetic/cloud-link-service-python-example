# Keenetic Cloud Link Service

## Setup Instructions

To be done

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

## Proxied errors from device

- **0x0300** -- No acknowledge after info request. (30 sec)
- **0x0400** -- Unable to get from or to send information to device. Is device off?
- **0x0143** -- Authorization was declined by Keenetic Device. Is device linked with provider?
