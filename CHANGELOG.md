# CHANGELOG

This is a manually generated log to track changes to the repository for each release.
Each section should include general headers such as **Implemented enhancements**
and **Merged pull requests**. Critical items to know are:

 - renamed commands
 - deprecated / removed commands
 - changed defaults
 - backward incompatible changes (recipe file format? image file format?)
 - migration guidance (how to convert images?)
 - changed behaviour (recipe sections work differently)

The versions coincide with releases on pip. Only major versions will be released as tags on Github.

## [0.0.x](https://github.scom/vsoch/elfcall/tree/main) (0.0.x)
 - best effort guess if an ELF binary is stripped (0.0.16)
  - addition of debug link property
 - tweaks to ld library path logic (0.0.15)
 - typo use_versions instead of user_versions (0.0.14)
 - add default argument to not use symbol versions (0.0.13)
 - add support to provide custom LD_LIBRARY_PATH (0.0.12)
   - loosen matching constaint to not include type
 - Bugfix in function name (0.0.11)
 - Fixing bug in name of utils function (0.0.1)
 - Initial creation of project (0.0.0)

