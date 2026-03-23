# Security Policy

## Supported Versions

SQLite Workbench is currently maintained as a single active development branch.

| Version | Supported |
|---------|-----------|
| Current | Yes       |
| Older releases | No |

## Reporting a Vulnerability

If you believe you have found a security issue in SQLite Workbench, please report it privately and responsibly.

Please include, if possible:

- a clear description of the issue
- affected version or commit
- steps to reproduce
- proof of concept, if available
- potential impact
- any suggested mitigation

## Contact

Please report security issues to:

**Carlos Costa**  
Project maintainer

Until a dedicated security contact address is created, security reports should be submitted through one of the following private channels:

- GitHub private security reporting, if enabled for the repository
- direct private contact with the maintainer

## Disclosure Policy

Please do not disclose security vulnerabilities publicly before they have been reviewed and, where appropriate, fixed.

The project will aim to:

- acknowledge receipt of the report
- assess the issue
- determine severity and scope
- prepare a fix when justified
- publish a correction in a future release

## Scope

Security issues may include, for example:

- unsafe handling of SQLite database files
- unsafe file import or export behavior
- unintended execution paths through SQL tooling
- insecure storage of local settings or history
- packaging or dependency-related issues
- privilege, path, or file overwrite issues

## Notes

SQLite Workbench is a local desktop application intended for opening and working with SQLite databases. Users should avoid opening untrusted files unless they understand the associated risks.

This project is provided on an "as is" basis under the MIT License, but responsible disclosure of genuine security issues is welcome and appreciated.