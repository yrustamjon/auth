# BioGuard device registration helper

This is a standalone, one-run pre-registration program, not the BioGuard Agent. It reads platform identifiers and sends them to a five-minute browser enrollment session. No Agent code, private key, password, biometric data, or permanent token is bundled.

Build all six OS/architecture variants with `make build` (Go 1.25+). The Django server reads binaries from `registration-helper/dist/`; do this build during deployment. On `/device/scan`, click **Scan this PC**, download the generated ZIP, extract it, then run `run-registration.cmd` (Windows), `run-registration.command` (macOS), or `run-registration.sh` (Linux). The browser polls and shows the QR only after the helper successfully submits the identifiers. The helper does not install a service or remain running.

Windows reads `MachineGuid` and `ProductId` from the registry. macOS reads `IOPlatformUUID` and `IOPlatformSerialNumber` using `ioreg`. Linux reads `/etc/machine-id` and, when available, `/sys/class/dmi/id/product_uuid`. A missing primary ID fails closed. Values are only unverified device metadata; an administrator must review them and later Agent enrollment must establish cryptographic device identity. The helper's short-lived scan token in `scan.json` is single-use and should not be shared. Remove the extracted 
bundle after enrollment.

For production distribution, sign the Windows binaries and sign/notarize the macOS binaries before making them available through Django. Unsigned builds are only suitable for development/testing; Windows SmartScreen or macOS Gatekeeper may warn or block them. The website cannot silently install or run a downloaded binary.
