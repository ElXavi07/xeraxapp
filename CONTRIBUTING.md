# Contributing to Xerax Root

Thank you for helping make Android modification workflows more transparent and
recoverable.

## Ground Rules

- Work only with devices you own or are authorized to modify.
- Do not submit lock-screen, FRP, account, activation, MDM, carrier, or payment
  security bypasses.
- Do not add arbitrary shell execution or weaken consent and verification gates.
- Do not label a device profile `tested` without evidence from matching physical
  hardware and firmware.
- Never commit API keys, device identifiers, proprietary firmware, or user data.

## Development

Run the tests before opening a pull request:

```powershell
python -m unittest discover -s tests -v
```

Keep changes focused and include tests for new parsing, validation, profiles, or
troubleshooting behavior. Device profile contributions should document the exact
product identifier, firmware fingerprint, target partition, commands observed,
and recovery result, with personal identifiers removed.

## Pull Requests

Explain the problem, the approach, verification performed, and any device-specific
risk. Changes affecting flashing, partition selection, firmware matching, or
unlock checks require especially careful tests and review.
