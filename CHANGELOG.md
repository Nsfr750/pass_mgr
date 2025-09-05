# Changelog

All notable changes to the Password Manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-04

### Added
- Initial release of Password Manager
- Secure password storage with AES-256 encryption
- Master password protection
- Basic password generation
- Simple search functionality
- Basic import/export capabilities
- Cross-browser extension (Chrome, Firefox, Opera)
- Auto-fill login forms with a single click
- Save new logins directly from the browser
- Generate strong passwords in the browser
- Native messaging host for secure communication
- Browser extension settings page
- Support for multiple browser profiles
- Automatic form detection and filling
- Secure password generation in the browser
- Browser action popup with quick access to features
- Native app integration for enhanced security

### Fixed
- Fixed toolbar button states
- Improved error handling in refresh operations
- Fixed dashboard initialization
- Resolved issues with special characters in passwords
- Fixed memory leaks in the native messaging host

### Changed
- Refactored codebase for better maintainability
- Updated dependencies to latest versions
- Improved security of the native messaging protocol
- Enhanced error handling and logging
- Optimized performance for large password databases

### Security
- Implemented secure password hashing with Argon2
- Secure storage of encrypted data
- Memory protection for sensitive data

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/Nsfr750/pass_mgr/tags).

## Authors

- **Nsfr750** - *Initial work* - [GitHub](https://github.com/Nsfr750)

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all contributors who have helped with this project
- Inspired by existing password managers like Bitwarden and KeePass
